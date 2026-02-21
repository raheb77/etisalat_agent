from fastapi.testclient import TestClient

from app.main import app
from app.services.query_cache import NEGATIVE_CACHE, build_cache_key


client = TestClient(app)


def _reset_negative_cache() -> None:
    with NEGATIVE_CACHE._lock:
        NEGATIVE_CACHE._data.clear()
        NEGATIVE_CACHE._order.clear()


def _get_metrics() -> dict:
    resp = client.get("/metrics")
    assert resp.status_code == 200
    return resp.json()


def _sum_counters(metrics: dict, prefix: str) -> int:
    counters = metrics.get("counters", {})
    total = 0
    if isinstance(counters, dict):
        for key, value in counters.items():
            if isinstance(key, str) and key.startswith(prefix) and isinstance(value, int):
                total += value
    return total


def test_negative_cache_used():
    _reset_negative_cache()
    payload = {
        "question": "اختبار",
        "locale": "ar-SA",
        "channel": "test_negative_cache",
    }
    metrics_before = _get_metrics()
    hits_before = _sum_counters(metrics_before, "negative_cache_hit_total")
    resp1 = client.post("/query", json=payload)
    assert resp1.status_code == 200
    body1 = resp1.json()

    cache_key = build_cache_key(payload["question"], payload["locale"], payload["channel"])
    cached = NEGATIVE_CACHE.get(cache_key)
    assert cached is not None

    resp2 = client.post("/query", json=payload)
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["answer"] == body1["answer"]
    assert body2["confidence"] == body1["confidence"]
    metrics_after = _get_metrics()
    hits_after = _sum_counters(metrics_after, "negative_cache_hit_total")
    assert hits_after >= hits_before + 1


def test_cached_requests_not_rate_limited_quickly():
    _reset_negative_cache()
    payload = {
        "question": "اختبار",
        "locale": "ar-SA",
        "channel": "test_rate_limit_cache",
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    for _ in range(20):
        resp = client.post("/query", json=payload)
        assert resp.status_code != 429
