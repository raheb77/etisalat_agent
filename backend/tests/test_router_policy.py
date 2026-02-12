from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_query_unknown_category_escalates():
    payload = {
        "question": "ما هي الباقة الأنسب؟",
        "category_hint": "unknown",
        "locale": "ar-SA",
        "channel": "csr_ui",
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["handoff"] is True
    assert body["category"] == "unknown"


def test_query_legal_escalates():
    payload = {
        "question": "أريد تفسير قانوني",
        "category_hint": "legal",
        "locale": "ar-SA",
        "channel": "csr_ui",
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["handoff"] is True
    assert body["category"] == "legal"
