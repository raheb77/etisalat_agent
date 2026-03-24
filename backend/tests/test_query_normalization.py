import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rag.normalize import normalize_query
from app.services import facts as facts_module
from app.services.query_cache import NEGATIVE_CACHE, POSITIVE_CACHE


client = TestClient(app)
FIXTURE_FACTS_DIR = Path(__file__).resolve().parent / "fixtures" / "facts"
REAL_FACTS_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "facts"


def _reset_cache() -> None:
    with POSITIVE_CACHE._lock:
        POSITIVE_CACHE._data.clear()
        POSITIVE_CACHE._order.clear()
    with NEGATIVE_CACHE._lock:
        NEGATIVE_CACHE._data.clear()
        NEGATIVE_CACHE._order.clear()


@pytest.fixture
def real_facts(monkeypatch):
    monkeypatch.setenv("FACTS_DIR", str(REAL_FACTS_DIR))
    importlib.reload(facts_module)
    _reset_cache()
    yield
    monkeypatch.setenv("FACTS_DIR", str(FIXTURE_FACTS_DIR))
    importlib.reload(facts_module)
    _reset_cache()


def _post_query(question: str) -> dict:
    payload = {
        "question": question,
        "locale": "ar-SA",
        "channel": "csr_ui",
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    return response.json()


def _confidence_pct(body: dict) -> int:
    value = body.get("confidence", 0)
    if isinstance(value, (int, float)):
        if value <= 1:
            return int(round(value * 100))
        return int(round(value))
    return 0


def test_normalize_query_arabic_and_alias_rules() -> None:
    assert normalize_query("ما مده نقل الرقم") == "ما مدة نقل الرقم"
    assert normalize_query("ما مُدّة نَقل الرّقم؟") == "ما مدة نقل الرقم"
    assert normalize_query("Porting duration كم؟") == "نقل الرقم مدة كم"
    assert normalize_query("كم ساعة يحتاج نقل الرقم كحد أقصى؟") == "ما مدة نقل الرقم"
    assert normalize_query("وش سعر عرض ٥٥ جيجا؟") == "وش سعر باقة 55 جيجا"
    assert normalize_query("كم تكلفة باقة 55GB؟") == "كم تكلفة باقة 55 gb"


def test_query_with_diacritics_routes_to_porting(real_facts) -> None:
    body = _post_query("ما مُدّة نَقل الرّقم؟")
    assert body.get("category") == "porting"
    assert "غير واضح" not in body.get("answer", "")


def test_query_rephrased_porting_duration_improves_retrieval(real_facts) -> None:
    body = _post_query("كم يستغرق تحويل رقمي من شركة إلى أخرى؟")
    assert body.get("category") == "porting"
    assert "غير واضح" not in body.get("answer", "")


def test_query_mixed_porting_phrase_is_not_ambiguous(real_facts) -> None:
    body = _post_query("Porting duration كم؟")
    assert body.get("category") == "porting"
    assert "غير واضح" not in body.get("answer", "")
    assert "لم نجد معلومات محددة" not in body.get("answer", "")
    assert len(body.get("citations", []) or []) >= 1 or _confidence_pct(body) > 35


def test_query_porting_max_hours_paraphrase_improves_retrieval(real_facts) -> None:
    body = _post_query("كم ساعة يحتاج نقل الرقم كحد أقصى؟")
    assert body.get("category") == "porting"
    assert body.get("handoff") is False
    assert "لم نجد معلومات محددة" not in body.get("answer", "")
    assert len(body.get("citations", []) or []) >= 1 or _confidence_pct(body) > 35


def test_query_offer_alias_hits_55gb_fact() -> None:
    body = _post_query("وش سعر عرض 55 جيجا؟")
    assert len(body.get("citations", []) or []) >= 1 or _confidence_pct(body) >= 60


def test_query_mixed_55gb_text_keeps_plan_match() -> None:
    body = _post_query("كم تكلفة باقة 55GB؟")
    assert len(body.get("citations", []) or []) >= 1 or _confidence_pct(body) >= 60
