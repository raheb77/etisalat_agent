import json
from pathlib import Path

from app.services import audit


def test_audit_redaction(tmp_path, monkeypatch):
    def fake_log_path():
        return tmp_path / "audit.log"

    monkeypatch.setattr(audit, "_audit_log_path", fake_log_path)

    audit.log_event(
        {
            "user_id": "u1",
            "category": "billing",
            "risk_level": "low",
            "confidence": 0.9,
            "handoff": False,
            "latency_ms": 10,
            "pii_detected": True,
            "sanitized_question": "***",
            "question": "0500000000",
        }
    )

    data = json.loads((tmp_path / "audit.log").read_text(encoding="utf-8").splitlines()[0])
    assert "question" not in data
    assert "question_hash" in data
