from __future__ import annotations

import threading
from collections import deque
from typing import Deque, Dict, List, Tuple

_LOCK = threading.Lock()
_COUNTERS: Dict[str, int] = {}
_LATENCIES: Dict[str, Deque[int]] = {}
_MAX_SAMPLES = 500


def _normalize_labels(labels: Dict[str, str] | None) -> Tuple[Tuple[str, str], ...]:
    if not labels:
        return tuple()
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


def _metric_key(name: str, labels: Dict[str, str] | None) -> str:
    normalized = _normalize_labels(labels)
    if not normalized:
        return name
    labels_repr = ",".join([f"{k}={v}" for k, v in normalized])
    return f"{name}{{{labels_repr}}}"


def inc_counter(name: str, labels: Dict[str, str] | None = None, value: int = 1) -> None:
    key = _metric_key(name, labels)
    with _LOCK:
        _COUNTERS[key] = _COUNTERS.get(key, 0) + int(value)


def observe_ms(name: str, value_ms: int, labels: Dict[str, str] | None = None) -> None:
    key = _metric_key(name, labels)
    sample = int(value_ms)
    with _LOCK:
        if key not in _LATENCIES:
            _LATENCIES[key] = deque(maxlen=_MAX_SAMPLES)
        _LATENCIES[key].append(sample)


def _percentile(values: List[int], pct: float) -> int:
    if not values:
        return 0
    values_sorted = sorted(values)
    if len(values_sorted) == 1:
        return values_sorted[0]
    index = int(round((pct / 100.0) * (len(values_sorted) - 1)))
    index = max(0, min(index, len(values_sorted) - 1))
    return values_sorted[index]


def snapshot() -> dict:
    with _LOCK:
        counters = dict(_COUNTERS)
        latencies = {k: list(v) for k, v in _LATENCIES.items()}

    latency_stats = {}
    for key, samples in latencies.items():
        if not samples:
            latency_stats[key] = {"count": 0, "min": 0, "max": 0, "p50": 0, "p95": 0}
            continue
        latency_stats[key] = {
            "count": len(samples),
            "min": min(samples),
            "max": max(samples),
            "p50": _percentile(samples, 50),
            "p95": _percentile(samples, 95),
        }

    return {
        "counters": counters,
        "latency_ms": latency_stats,
    }
