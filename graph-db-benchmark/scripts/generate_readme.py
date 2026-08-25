import json
import argparse
from pathlib import Path
from typing import List, Dict, Any


def fmt(val, decimals=2):
    if isinstance(val, (int, float)):
        return f"{val:.{decimals}f}"
    return str(val)


def generate_markdown_tables(results: List[Dict[str, Any]], output_path: str):
    lines = []
    lines.append("## Data Loading\n")
    lines.append("| Database | Nodes/sec | Rels/sec | Wall-clock time |")
    lines.append("|----------|-----------|----------|-----------------|")
    for r in results:
        if "error" in r:
            lines.append(f"| {r['database']} | ERROR | ERROR | {r['error']} |")
            continue
        lines.append(f"| {r['database']} | - | - | - |")
    lines.append("")

    lines.append("## Traversals (p50 / p95 latency in ms)\n")
    lines.append("| Database | 1-hop p50 | 1-hop p95 | 2-hop p50 | 2-hop p95 | 3-hop p50 | 3-hop p95 |")
    lines.append("|----------|-----------|-----------|-----------|-----------|-----------|-----------|")
    for r in results:
        if "error" in r:
            lines.append(f"| {r['database']} | - | - | - | - | - | - |")
            continue
        t = r.get("traversals", {})
        h1 = t.get("1_hop", {})
        h2 = t.get("2_hop", {})
        h3 = t.get("3_hop", {})
        lines.append(
            f"| {r['database']} "
            f"| {fmt(h1.get('p50', '-'))} | {fmt(h1.get('p95', '-'))} "
            f"| {fmt(h2.get('p50', '-'))} | {fmt(h2.get('p95', '-'))} "
            f"| {fmt(h3.get('p50', '-'))} | {fmt(h3.get('p95', '-'))} |"
        )
    lines.append("")

    lines.append("## Lookups (p50 / p95 latency in ms)\n")
    lines.append("| Database | Point p50 | Point p95 | Indexed p50 | Indexed p95 |")
    lines.append("|----------|-----------|-----------|-------------|-------------|")
    for r in results:
        if "error" in r:
            lines.append(f"| {r['database']} | - | - | - | - |")
            continue
        l = r.get("lookups", {})
        pt = l.get("point", {})
        ix = l.get("indexed", {})
        lines.append(
            f"| {r['database']} "
            f"| {fmt(pt.get('p50', '-'))} | {fmt(pt.get('p95', '-'))} "
            f"| {fmt(ix.get('p50', '-'))} | {fmt(ix.get('p95', '-'))} |"
        )
    lines.append("")

    lines.append("## Aggregations (p50 / p95 latency in ms)\n")
    lines.append("| Database | p50 | p95 |")
    lines.append("|----------|-----|-----|")
    for r in results:
        if "error" in r:
            lines.append(f"| {r['database']} | - | - |")
            continue
        a = r.get("aggregations", {})
        lines.append(f"| {r['database']} | {fmt(a.get('p50', '-'))} | {fmt(a.get('p95', '-'))} |")
    lines.append("")

    lines.append("## Mixed Workload (queries/sec)\n")
    for conc in ["1", "10", "40"]:
        lines.append(f"### Concurrency = {conc}\n")
        lines.append("| Database | Ops/sec | Total ops | Time (sec) |")
        lines.append("|----------|---------|-----------|------------|")
        for r in results:
            if "error" in r:
                lines.append(f"| {r['database']} | - | - | - |")
                continue
            m = r.get("mixed_workload", {}).get(conc, {})
            lines.append(
                f"| {r['database']} "
                f"| {fmt(m.get('ops_per_sec', '-'))} "
                f"| {fmt(m.get('total_ops', '-'), 0)} "
                f"| {fmt(m.get('total_time_sec', '-'))} |"
            )
        lines.append("")

    lines.append("## Footprint\n")
    lines.append("| Database | Nodes | Relationships | Notes |")
    lines.append("|----------|-------|---------------|-------|")
    for r in results:
        if "error" in r:
            lines.append(f"| {r['database']} | - | - | {r['error']} |")
            continue
        f = r.get("footprint", {})
        if isinstance(f, dict):
            lines.append(f"| {r['database']} | {f.get('nodes', '-')} | {f.get('relationships', '-')} | see README |")
        else:
            lines.append(f"| {r['database']} | - | - | not observable |")
    lines.append("")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown results written to {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/benchmark_results.json")
    parser.add_argument("--output", default="results/results_tables.md")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        results = json.load(f)
    generate_markdown_tables(results, args.output)


if __name__ == "__main__":
    main()
