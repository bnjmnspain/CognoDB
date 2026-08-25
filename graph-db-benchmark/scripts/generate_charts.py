import json
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def load_results(path: str):
    with open(path, "r") as f:
        return json.load(f)


def plot_traversals(results, output_dir: Path):
    dbs = [r["database"] for r in results if "error" not in r]
    categories = ["1_hop", "2_hop", "3_hop"]
    x = np.arange(len(dbs))
    width = 0.35

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for idx, cat in enumerate(categories):
        ax = axes[idx]
        p50 = [r["traversals"].get(cat, {}).get("p50", 0) for r in results if "error" not in r]
        p95 = [r["traversals"].get(cat, {}).get("p95", 0) for r in results if "error" not in r]
        ax.bar(x - width/2, p50, width, label="p50")
        ax.bar(x + width/2, p95, width, label="p95")
        ax.set_title(f"{cat.replace('_', ' ').title()} Traversal Latency")
        ax.set_ylabel("Latency (ms)")
        ax.set_xticks(x)
        ax.set_xticklabels(dbs, rotation=45, ha="right")
        ax.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "traversals.png", dpi=150)
    plt.close()


def plot_lookups(results, output_dir: Path):
    dbs = [r["database"] for r in results if "error" not in r]
    x = np.arange(len(dbs))
    width = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for idx, key in enumerate(["point", "indexed"]):
        ax = axes[idx]
        p50 = [r["lookups"].get(key, {}).get("p50", 0) for r in results if "error" not in r]
        p95 = [r["lookups"].get(key, {}).get("p95", 0) for r in results if "error" not in r]
        ax.bar(x - width/2, p50, width, label="p50")
        ax.bar(x + width/2, p95, width, label="p95")
        ax.set_title(f"{key.capitalize()} Lookup Latency")
        ax.set_ylabel("Latency (ms)")
        ax.set_xticks(x)
        ax.set_xticklabels(dbs, rotation=45, ha="right")
        ax.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "lookups.png", dpi=150)
    plt.close()


def plot_aggregations(results, output_dir: Path):
    dbs = [r["database"] for r in results if "error" not in r]
    p50 = [r["aggregations"].get("p50", 0) for r in results if "error" not in r]
    p95 = [r["aggregations"].get("p95", 0) for r in results if "error" not in r]
    x = np.arange(len(dbs))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width/2, p50, width, label="p50")
    ax.bar(x + width/2, p95, width, label="p95")
    ax.set_title("Aggregation Latency")
    ax.set_ylabel("Latency (ms)")
    ax.set_xticks(x)
    ax.set_xticklabels(dbs, rotation=45, ha="right")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "aggregations.png", dpi=150)
    plt.close()


def plot_mixed(results, output_dir: Path):
    dbs = [r["database"] for r in results if "error" not in r]
    concurrencies = ["1", "10", "40"]
    x = np.arange(len(dbs))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, conc in enumerate(concurrencies):
        vals = [r["mixed_workload"].get(conc, {}).get("ops_per_sec", 0) for r in results if "error" not in r]
        ax.bar(x + i*width - width, vals, width, label=f"{conc} clients")
    ax.set_title("Mixed Workload Throughput")
    ax.set_ylabel("Ops/sec")
    ax.set_xticks(x)
    ax.set_xticklabels(dbs, rotation=45, ha="right")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "mixed_workload.png", dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/benchmark_results.json")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = load_results(args.input)
    plot_traversals(results, output_dir)
    plot_lookups(results, output_dir)
    plot_aggregations(results, output_dir)
    plot_mixed(results, output_dir)
    print(f"Charts saved to {output_dir}")


if __name__ == "__main__":
    main()
