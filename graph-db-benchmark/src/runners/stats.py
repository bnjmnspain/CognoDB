import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import random


class MixedWorkload:
    def __init__(self, runner, start_nodes: List[int], duration_sec: int = 30):
        self.runner = runner
        self.start_nodes = start_nodes
        self.duration_sec = duration_sec
        self.rng = random.Random(42)

    def _reader_loop(self, results: list):
        count = 0
        end_time = time.perf_counter() + self.duration_sec
        while time.perf_counter() < end_time:
            try:
                nid = self.rng.choice(self.start_nodes)
                self.runner.run_query("traversals", {"id": nid})
                count += 1
            except Exception:
                pass
        results.append(count)

    def _writer_loop(self, results: list):
        count = 0
        end_time = time.perf_counter() + self.duration_sec
        while time.perf_counter() < end_time:
            try:
                self.runner.loader.create_schema()
                count += 1
            except Exception:
                pass
        results.append(count)

    def run(self, concurrency: int) -> Dict[str, Any]:
        reader_counts = []
        writer_counts = []
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for _ in range(concurrency):
                r = []
                futures.append(executor.submit(self._reader_loop, r))
                reader_counts.append(r)
            for _ in range(max(1, concurrency // 4)):
                w = []
                futures.append(executor.submit(self._writer_loop, w))
                writer_counts.append(w)
            for f in as_completed(futures):
                f.result()
        total_time = time.perf_counter() - start
        total_ops = sum(sum(c) for c in reader_counts) + sum(sum(c) for c in writer_counts)
        return {
            "concurrency": concurrency,
            "ops_per_sec": round(total_ops / total_time, 2) if total_time > 0 else 0,
            "total_ops": total_ops,
            "total_time_sec": round(total_time, 4),
        }
