import os
import time
import random
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from .timing import summarize_latencies


class QueryRunner:
    def __init__(self, loader, db_type: str, queries_dir: str = "queries"):
        self.loader = loader
        self.db_type = db_type.lower()
        self.queries_dir = queries_dir
        self.random = random.Random(42)

    def _read_query(self, name: str) -> str:
        ext_map = {"cognodb": "cyp", "neo4j": "cyp", "memgraph": "cyp", "neptune": "grm", "arangodb": "aql"}
        ext = ext_map.get(self.db_type, "txt")
        path = os.path.join(self.queries_dir, self.db_type, f"{name}.{ext}")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Query file not found: {path}")
        with open(path, "r") as f:
            return f.read().strip()

    def _execute_cypher(self, query: str, params: dict):
        with self.loader.driver.session(database=self.loader.config.get("database", "neo4j")) as session:
            return session.run(query, **params).data()

    def _execute_gremlin(self, query: str, params: dict):
        if "id" in params:
            query = query.replace("id", str(params["id"]))
        result = self.loader.client.submit(query).all().result()
        return result

    def _execute_aql(self, query: str, params: dict):
        cursor = self.loader.db.aql.execute(query, bind_vars=params, batch_size=1000)
        return [doc for doc in cursor]

    def run_query(self, query_name: str, params: dict) -> Any:
        query = self._read_query(query_name)
        if self.db_type in ("cognodb", "neo4j", "memgraph"):
            return self._execute_cypher(query, params)
        elif self.db_type == "neptune":
            return self._execute_gremlin(query, params)
        elif self.db_type == "arangodb":
            return self._execute_aql(query, params)
        else:
            raise ValueError(f"Unsupported db_type: {self.db_type}")

    def run_traversals(self, start_nodes: List[int], iterations: int = 100) -> Dict[str, dict]:
        results = {}
        for hop, name in [(1, "traversals"), (2, "traversals_2hop"), (3, "traversals_3hop")]:
            latencies = []
            for _ in range(iterations):
                nid = self.random.choice(start_nodes)
                start = time.perf_counter()
                try:
                    self.run_query(name, {"id": nid})
                except Exception:
                    pass
                end = time.perf_counter()
                latencies.append((end - start) * 1000.0)
            results[f"{hop}_hop"] = summarize_latencies(latencies)
        return results

    def run_lookups(self, start_nodes: List[int], iterations: int = 100) -> Dict[str, dict]:
        results = {}
        for name, indexed in [("lookups", False), ("lookups_indexed", True)]:
            latencies = []
            for _ in range(iterations):
                nid = self.random.choice(start_nodes)
                start = time.perf_counter()
                try:
                    self.run_query(name, {"id": nid})
                except Exception:
                    pass
                end = time.perf_counter()
                latencies.append((end - start) * 1000.0)
            results["point" if not indexed else "indexed"] = summarize_latencies(latencies)
        return results

    def run_aggregations(self, iterations: int = 100) -> Dict[str, dict]:
        latencies = []
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                self.run_query("aggregations", {})
            except Exception:
                pass
            end = time.perf_counter()
            latencies.append((end - start) * 1000.0)
        return summarize_latencies(latencies)

    def warmup(self, start_nodes: List[int], iterations: int = 10):
        for _ in range(iterations):
            nid = self.random.choice(start_nodes)
            try:
                self.run_query("traversals", {"id": nid})
                self.run_query("lookups", {"id": nid})
                self.run_query("aggregations", {})
            except Exception:
                pass
