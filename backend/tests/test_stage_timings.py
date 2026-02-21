import json
import logging

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_stage_timings_in_telemetry(caplog):
    caplog.set_level(logging.INFO, logger="app.telemetry")
    payload = {
        "question": "كم سعر باقة 55 جيجا؟",
        "locale": "ar-SA",
        "channel": "csr_ui",
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200

    telemetry_records = [
        record for record in caplog.records if record.name == "app.telemetry"
    ]
    assert telemetry_records, "No telemetry logs captured"
    data = json.loads(telemetry_records[-1].message)
    assert "timings_ms" in data
    timings = data["timings_ms"]
    assert timings.get("total", 0) > 0
    assert any(timings.get(stage, 0) > 0 for stage in ["intent", "retrieve", "rank", "answer"])


def test_stage_timings_cache_hit(caplog):
    caplog.set_level(logging.INFO, logger="app.telemetry")
    payload = {
        "question": "كم سعر باقة 55 جيجا؟",
        "locale": "ar-SA",
        "channel": "timing_cache",
    }
    resp1 = client.post("/query", json=payload)
    assert resp1.status_code == 200
    caplog.clear()
    resp2 = client.post("/query", json=payload)
    assert resp2.status_code == 200

    telemetry_records = [
        record for record in caplog.records if record.name == "app.telemetry"
    ]
    assert telemetry_records, "No telemetry logs captured on cache hit"
    data = json.loads(telemetry_records[-1].message)
    timings = data.get("timings_ms", {})
    assert timings.get("total", 0) > 0
    assert timings.get("cache_hit", 0) > 0 or timings.get("skipped") is True
