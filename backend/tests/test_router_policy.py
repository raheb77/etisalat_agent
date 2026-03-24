import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import facts as facts_module


client = TestClient(app)
FIXTURE_FACTS_DIR = Path(__file__).resolve().parent / "fixtures" / "facts"
REAL_FACTS_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "facts"


@pytest.fixture
def real_facts(monkeypatch):
    monkeypatch.setenv("FACTS_DIR", str(REAL_FACTS_DIR))
    importlib.reload(facts_module)
    yield
    monkeypatch.setenv("FACTS_DIR", str(FIXTURE_FACTS_DIR))
    importlib.reload(facts_module)


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


def test_query_legal_factual_lookup_with_evidence_does_not_escalate(real_facts):
    payload = {
        "question": "ما المدة القانونية القصوى لنقل رقم الهاتف المتنقل؟",
        "locale": "ar-SA",
        "channel": "csr_ui",
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "porting"
    assert body["handoff"] is False
    assert body["confidence"] >= 0.6 or len(body["citations"]) >= 1


def test_query_complaint_escalates():
    payload = {
        "question": "أبغى أشتكي على الشركة رسميًا",
        "locale": "ar-SA",
        "channel": "csr_ui",
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "complaints"
    assert body["handoff"] is True


def test_query_security_compromise_escalates():
    payload = {
        "question": "تم اختراق رقمي وأحتاج إجراء عاجل",
        "locale": "ar-SA",
        "channel": "csr_ui",
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["handoff"] is True
    assert body["category"] == "security"
