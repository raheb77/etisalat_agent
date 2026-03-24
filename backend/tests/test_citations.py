from app.core.citations import build_citations
from app.services.facts import FactHit
from app.services.retrieval import ContextChunk


def test_citations_internal_paths_only():
    facts = [
        FactHit(
            statement="x",
            values="1",
            source="docs/topics/billing-disputes.md",
            matched_terms=[],
            tags=["billing"],
            score=0.3,
        ),
        FactHit(
            statement="y",
            values="2",
            source="https://example.com",
            matched_terms=[],
            tags=["billing"],
            score=0.3,
        ),
    ]
    chunks = [
        ContextChunk(
            source="docs/index.md",
            chunk_id="c1",
            score=0.8,
            text="تفاصيل إضافية من المستند الداخلي.",
        ),
        ContextChunk(
            source="http://bad.example",
            chunk_id="c2",
            score=0.5,
            text="",
        ),
    ]

    citations = build_citations(facts, chunks)
    assert len(citations) == 2
    assert citations[0].source == "docs/index.md"
    assert citations[0].chunk_id == "c1"
    assert citations[0].snippet == "تفاصيل إضافية من المستند الداخلي."
    assert citations[1].source == "docs/topics/billing-disputes.md"
    assert citations[1].snippet == "x 1"


def test_citations_dedupe_keeps_highest_score_and_snippet():
    facts = [
        FactHit(
            statement="سعر الباقة الأساسية",
            values="100 ريال",
            source="docs/plans.md",
            matched_terms=[],
            tags=["plans"],
            score=0.4,
        ),
        FactHit(
            statement="سعر الباقة الأساسية",
            values="100 ريال",
            source="docs/plans.md",
            matched_terms=[],
            tags=["plans"],
            score=0.9,
        ),
    ]
    chunks = [
        ContextChunk(
            source="docs/plans.md",
            chunk_id="c1",
            score=0.2,
            text="نص قصير",
        ),
        ContextChunk(
            source="docs/plans.md",
            chunk_id="c1",
            score=0.7,
            text="نص قصير أفضل",
        ),
    ]

    citations = build_citations(facts, chunks)
    assert len(citations) == 2
    assert citations[0].source == "docs/plans.md"
    assert citations[0].chunk_id == "fact"
    assert citations[0].score == 0.9
    assert citations[0].snippet == "سعر الباقة الأساسية 100 ريال"
    assert citations[1].source == "docs/plans.md"
    assert citations[1].chunk_id == "c1"
    assert citations[1].score == 0.7
    assert citations[1].snippet == "نص قصير أفضل"
