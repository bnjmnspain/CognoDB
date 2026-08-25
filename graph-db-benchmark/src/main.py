import os
import sys
import json
import yaml
import argparse
from typing import List, Dict, Any
from datetime import datetime

from src.dataset.downloader import get_dataset
from src.loaders.cognodb import CognoDBLoader
from src.loaders.neo4j import Neo4jLoader
from src.loaders.neptune import NeptuneLoader
from src.loaders.arangodb import ArangoDBLoader
from src.loaders.memgraph import MemgraphLoader
from src.runners.workload import QueryRunner
from src.runners.stats import MixedWorkload


LOADER_MAP = {
    "cognodb": CognoDBLoader,
    "neo4j": Neo4jLoader,
    "neptune": NeptuneLoader,
    "arangodb": ArangoDBLoader,
    "memgraph": MemgraphLoader,
}


def get_start_nodes(loader, db_type: str, count: int = 1000) -> List[int]:
    nodes = []
    try:
        if db_type in ("cognodb", "neo4j", "memgraph"):
            with loader.driver.session(database=loader.config.get("database", "neo4j")) as session:
                result = session.run("MATCH (n:User) RETURN n.id AS id LIMIT $count", count=count * 10)
                nodes = [record["id"] for record in result]
        elif db_type == "arangodb":
            cursor = loader.db.aql.execute("FOR u IN users LIMIT @count RETURN u.id", bind_vars={"count": count * 10})
            nodes = [doc for doc in cursor]
        elif db_type == "neptune":
            result = loader.client.submit("g.V().hasLabel('User').values('id').limit(10000)").all().result()
            nodes = [int(x) for x in result[:count * 10]]
    except Exception as e:
        print(f"Warning: could not fetch start nodes for {db_type}: {e}")
    return nodes[:count] if nodes else list(range(1, count + 1))


def run_benchmark_for_db(db_name: str, db_config: dict, dataset_edges: List, global_config: dict, cold_start: bool = False) -> Dict[str, Any]:
    print(f"\n{'='*60}")
    print(f"Benchmarking {db_name}")
    print(f"{'='*60}")
    loader_cls = LOADER_MAP.get(db_name)
    if not loader_cls:
        return {"error": f"Unknown database: {db_name}"}

    loader = loader_cls(db_config)
    try:
        loader.connect()
        print(f"  Connected to {db_name}")
    except Exception as e:
        return {"error": f"Connection failed: {e}"}

    try:
        loader.create_schema()
        loader.clear()
        node_ids = sorted(set([s for s, _ in dataset_edges] + [t for _, t in dataset_edges]))
        print(f"  Loading {len(node_ids)} nodes...")
        loader.load_nodes(node_ids)
        print(f"  Loading {len(dataset_edges)} relationships...")
        loader.load_relationships(dataset_edges)
        loader.create_indexes()
        actual_nodes = loader.count_nodes()
        actual_rels = loader.count_relationships()
        print(f"  Verified: {actual_nodes} nodes, {actual_rels} relationships")
    except Exception as e:
        loader.close()
        return {"error": f"Data load failed: {e}"}

    runner = QueryRunner(loader, db_name)
    start_nodes = get_start_nodes(loader, db_name, count=1000)

    results = {
        "database": db_name,
        "timestamp": datetime.utcnow().isoformat(),
        "dataset": {
            "nodes": actual_nodes,
            "relationships": actual_rels,
        },
        "instance_specs": db_config.get("instance_specs", "see README"),
    }

    if cold_start:
        print("  Running cold-start measurements...")
        results["cold_start"] = {
            "traversals": runner.run_traversals(start_nodes, iterations=10),
            "lookups": runner.run_lookups(start_nodes, iterations=10),
            "aggregations": runner.run_aggregations(iterations=10),
        }

    runner.warmup(start_nodes, iterations=global_config.get("warmup_iterations", 10))

    results["traversals"] = runner.run_traversals(start_nodes, iterations=global_config.get("iterations", 100))
    results["lookups"] = runner.run_lookups(start_nodes, iterations=global_config.get("iterations", 100))
    results["aggregations"] = runner.run_aggregations(iterations=global_config.get("iterations", 100))
    results["mixed_workload"] = {}

    for concurrency in global_config.get("concurrency_levels", [1, 10, 40]):
        print(f"  Running mixed workload (concurrency={concurrency})...")
        mixed = MixedWorkload(runner, start_nodes, duration_sec=30)
        results["mixed_workload"][str(concurrency)] = mixed.run(concurrency)

    try:
        footprint = {
            "nodes": loader.count_nodes(),
            "relationships": loader.count_relationships(),
        }
        results["footprint"] = footprint
    except Exception:
        results["footprint"] = "not observable"

    loader.close()
    print(f"  Completed {db_name}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Graph Database Benchmark Harness")
    parser.add_argument("--config", default="config/databases.yaml", help="Path to config YAML")
    parser.add_argument("--databases", nargs="+", help="Databases to benchmark (default: all)")
    parser.add_argument("--output", default="results/benchmark_results.json", help="Output JSON path")
    parser.add_argument("--dataset-target", type=int, default=88234, help="Target number of relationships")
    parser.add_argument("--cold-start", action="store_true", help="Include cold-start measurements")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    global_config = config.get("benchmark", {})
    db_configs = config.get("databases", {})

    if args.databases:
        db_names = [k for k in args.databases if k in db_configs]
    else:
        db_names = list(db_configs.keys())

    print(f"Preparing dataset (target {args.dataset_target} relationships)...")
    edges = get_dataset(
        target_rels=args.dataset_target,
        seed=global_config.get("random_seed", 42),
    )

    all_results = []
    for db_name in db_names:
        result = run_benchmark_for_db(db_name, db_configs[db_name], edges, global_config, cold_start=args.cold_start)
        all_results.append(result)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {args.output}")
    return all_results


if __name__ == "__main__":
    main()
