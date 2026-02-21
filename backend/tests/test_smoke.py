from fastapi.testclient import TestClient

from app.main import app
from app.services.query_cache import NEGATIVE_CACHE, POSITIVE_CACHE, build_cache_key


client = TestClient(app)


def _reset_cache() -> None:
    with POSITIVE_CACHE._lock:
        POSITIVE_CACHE._data.clear()
        POSITIVE_CACHE._order.clear()
    with NEGATIVE_CACHE._lock:
        NEGATIVE_CACHE._data.clear()
        NEGATIVE_CACHE._order.clear()


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"


def test_query_ambiguous_path():
    payload = {"question": "عندي مشكلة", "locale": "ar-SA", "channel": "smoke"}
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("handoff") is False
    assert body.get("confidence") == 0.5
    assert body.get("citations") == []
    assert "غير واضح" in body.get("answer", "")


def test_query_known_answer_with_citations():
    payload = {"question": "كم سعر باقة 55 جيجا؟", "locale": "ar-SA", "channel": "smoke"}
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("confidence", 0) >= 0.6 or len(body.get("citations", [])) >= 1


def test_cache_hit_consistency():
    _reset_cache()
    payload = {"question": "كم سعر باقة 55 جيجا؟", "locale": "ar-SA", "channel": "smoke_cache"}
    resp1 = client.post("/query", json=payload)
    assert resp1.status_code == 200
    body1 = resp1.json()

    cache_key = build_cache_key(payload["question"], payload["locale"], payload["channel"])
    assert POSITIVE_CACHE.get(cache_key) is not None

    resp2 = client.post("/query", json=payload)
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2.get("answer") == body1.get("answer")
    assert body2.get("confidence") == body1.get("confidence")


def test_negative_cache_behavior():
    _reset_cache()
    payload = {"question": "اختبار", "locale": "ar-SA", "channel": "smoke_neg"}
    resp1 = client.post("/query", json=payload)
    assert resp1.status_code == 200
    body1 = resp1.json()

    cache_key = build_cache_key(payload["question"], payload["locale"], payload["channel"])
    assert NEGATIVE_CACHE.get(cache_key) is not None

    resp2 = client.post("/query", json=payload)
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2.get("answer") == body1.get("answer")


def test_rate_limit_sanity_with_cache():
    _reset_cache()
    payload = {"question": "اختبار", "locale": "ar-SA", "channel": "smoke_rate"}
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    for _ in range(20):
        resp = client.post("/query", json=payload)
        assert resp.status_code != 429
