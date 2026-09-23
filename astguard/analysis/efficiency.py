from __future__ import annotations

import statistics
import time


def benchmark(operation, repeats: int = 3) -> dict:
    values = []
    for _ in range(repeats):
        start = time.perf_counter()
        operation()
        values.append(time.perf_counter() - start)
    return {"repeats": repeats, "mean_seconds": statistics.mean(values), "median_seconds": statistics.median(values), "raw_seconds": values}

