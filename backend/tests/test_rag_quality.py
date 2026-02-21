"""
Run: pytest -k rag_quality
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _post_query(question: str, locale: str = "ar-SA") -> dict:
    payload = {
        "question": question,
        "locale": locale,
        "channel": "csr_ui",
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    return resp.json()


def _confidence_pct(body: dict) -> int:
    value = body.get("confidence", 0)
    if isinstance(value, (int, float)):
        if value <= 1:
            return int(round(value * 100))
        return int(round(value))
    return 0


def test_rag_oos():
    body = _post_query("ما أفضل هاتف في 2026؟")
    assert _confidence_pct(body) <= 30
    assert len(body.get("citations", [])) == 0
    assert body.get("handoff") is True
    answer = body.get("answer", "")
    assert "خارج نطاق" in answer or "Out of scope" in answer


def test_rag_ambiguous():
    body = _post_query("عندي مشكلة")
    assert len(body.get("citations", [])) == 0
    assert body.get("handoff") is False
    answer = body.get("answer", "")
    assert "توضيح" in answer or "clarify" in answer


def test_rag_plans_query():
    body = _post_query("كم سعر باقة 55 جيجا؟")
    citations_count = len(body.get("citations", []))
    confidence_pct = _confidence_pct(body)
    assert citations_count >= 1 or confidence_pct >= 60


def test_rag_weak_evidence():
    body = _post_query("ما رسوم نقل الملكية؟")
    citations_count = len(body.get("citations", []))
    confidence_pct = _confidence_pct(body)
    assert citations_count == 0 or confidence_pct == 20 or body.get("handoff") is True


def test_rag_fraud_intent():
    body = _post_query("تعرضت لاحتيال وسحب رصيد")
    category = body.get("category")
    assert category == "fraud" or body.get("handoff") is True
