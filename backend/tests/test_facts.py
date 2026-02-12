import importlib
import os


def test_search_facts_keyword_and_tag(tmp_path, monkeypatch):
    fixture_dir = "/Users/rahebalmutairi/Documents/Etisalat_agent/backend/tests/fixtures/facts"
    monkeypatch.setenv("FACTS_DIR", fixture_dir)

    from app.services import facts as facts_module
    importlib.reload(facts_module)

    hits = facts_module.search_facts("أحتاج معلومات عن الفاتورة", "billing")
    assert len(hits) >= 1
    assert hits[0].source == "docs/topics/billing-disputes.md"


def test_search_facts_keyword_match(monkeypatch):
    fixture_dir = "/Users/rahebalmutairi/Documents/Etisalat_agent/backend/tests/fixtures/facts"
    monkeypatch.setenv("FACTS_DIR", fixture_dir)

    from app.services import facts as facts_module
    importlib.reload(facts_module)

    hits = facts_module.search_facts("تغطية 5G", "network")
    assert len(hits) >= 1
    assert "تغطية" in hits[0].matched_terms or "5g" in hits[0].matched_terms
