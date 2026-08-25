import time
import statistics
from typing import List, Tuple


def measure_latencies(func, iterations: int, *args, **kwargs) -> List[float]:
    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        latencies.append((end - start) * 1000.0)
    return latencies


def percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return d0 + d1


def summarize_latencies(latencies: List[float]) -> dict:
    if not latencies:
        return {"p50": 0.0, "p95": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0, "count": 0}
    return {
        "p50": round(percentile(latencies, 50), 4),
        "p95": round(percentile(latencies, 95), 4),
        "mean": round(statistics.mean(latencies), 4),
        "min": round(min(latencies), 4),
        "max": round(max(latencies), 4),
        "count": len(latencies),
    }


def throughput_stats(durations: List[float], operations: int) -> dict:
    total_time = sum(durations)
    if total_time <= 0:
        return {"ops_per_sec": 0.0, "total_ops": operations, "total_time_sec": 0.0}
    return {
        "ops_per_sec": round(operations / total_time, 2),
        "total_ops": operations,
        "total_time_sec": round(total_time, 4),
    }
