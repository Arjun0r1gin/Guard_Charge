import time


def measure_latency(func, *args, **kwargs) -> tuple:
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, round(elapsed_ms, 2)


def ms_since(start_time: float) -> float:
    return round((time.perf_counter() - start_time) * 1000, 2)
    