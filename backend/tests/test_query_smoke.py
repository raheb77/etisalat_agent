from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_query_smoke_plan():
    payload = {
        "question": "أريد تغيير الباقة",
        "category_hint": "plans",
        "locale": "ar-SA",
        "channel": "csr_ui",
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    for field in [
        "answer",
        "steps",
        "citations",
        "confidence",
        "category",
        "risk_level",
        "handoff",
        "handoff_reason",
        "handoff_payload",
    ]:
        assert field in body

    for citation in body["citations"]:
        assert not citation["source"].startswith("http")


def test_query_handoff_keywords():
    for keyword in ["fraud", "security", "legal"]:
        payload = {
            "question": f"This is a {keyword} issue",
            "category_hint": "unknown",
            "locale": "ar-SA",
            "channel": "csr_ui",
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["handoff"] is True
