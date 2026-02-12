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
            text="",
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
    assert citations[0].source == "docs/topics/billing-disputes.md"
    assert citations[1].source == "docs/index.md"
    assert citations[1].chunk_id == "c1"
