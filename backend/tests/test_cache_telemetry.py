import json
import logging

from fastapi.testclient import TestClient

from app.main import app
from app.services.decision_result import DecisionResult
from app.services.query_cache import POSITIVE_CACHE, build_cache_key


client = TestClient(app)


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


def _reset_cache() -> None:
    with POSITIVE_CACHE._lock:
        POSITIVE_CACHE._data.clear()
        POSITIVE_CACHE._order.clear()


def test_cache_hit_preserves_telemetry(caplog):
    _reset_cache()
    caplog.set_level(logging.INFO, logger="app.telemetry")
    payload = {
        "question": "كم سعر باقة 55 جيجا؟",
        "locale": "ar-SA",
        "channel": "csr_ui",
    }
    resp1 = client.post("/query", json=payload)
    assert resp1.status_code == 200
    telemetry_records = [
        record for record in caplog.records if record.name == "app.telemetry"
    ]
    assert telemetry_records
    data1 = json.loads(telemetry_records[-1].message)
    assert data1.get("detected_intent") not in (None, "", "unknown")
    assert data1.get("intent_score") is not None
    caplog.clear()

    cache_key = build_cache_key(payload["question"], payload["locale"], payload["channel"])
    cached = POSITIVE_CACHE.get(cache_key)
    assert cached is not None
    decision1 = DecisionResult.from_cache(cached)
    assert decision1.decision_path
    assert decision1.telemetry.get("detected_intent") not in (None, "", "unknown")
    assert decision1.telemetry.get("top_score") is not None

    metrics_before = _get_metrics()
    hits_before = _sum_counters(metrics_before, "query_cache_hit_total")

    resp2 = client.post("/query", json=payload)
    assert resp2.status_code == 200
    telemetry_records = [
        record for record in caplog.records if record.name == "app.telemetry"
    ]
    assert telemetry_records
    data2 = json.loads(telemetry_records[-1].message)
    assert data2.get("cache_hit") is True
    assert data2.get("detected_intent") == data1.get("detected_intent")
    assert data2.get("intent_score") == data1.get("intent_score")

    metrics_after = _get_metrics()
    hits_after = _sum_counters(metrics_after, "query_cache_hit_total")
    assert hits_after >= hits_before + 1

    cached_again = POSITIVE_CACHE.get(cache_key)
    decision2 = DecisionResult.from_cache(cached_again)
    assert decision2.telemetry.get("detected_intent") == decision1.telemetry.get("detected_intent")
    assert decision2.telemetry.get("intent_score") == decision1.telemetry.get("intent_score")
    assert decision2.telemetry.get("top_score") == decision1.telemetry.get("top_score")
    assert decision2.decision_path == decision1.decision_path
