from typing import Iterable, List

from app.schemas.query import Citation
from app.services.facts import FactHit
from app.services.retrieval import ContextChunk

_MAX_CITATIONS = 4
_MAX_SNIPPET_CHARS = 140


def _is_internal_path(path: str) -> bool:
    return not (path.startswith("http://") or path.startswith("https://"))


def _snippet_preview(text: str) -> str | None:
    cleaned = " ".join(text.split()).strip()
    if not cleaned:
        return None
    if len(cleaned) <= _MAX_SNIPPET_CHARS:
        return cleaned
    return cleaned[: _MAX_SNIPPET_CHARS - 1].rstrip() + "…"


def _upsert_citation(citations: dict[tuple[str, str], Citation], citation: Citation) -> None:
    key = (citation.source, citation.chunk_id)
    existing = citations.get(key)
    if existing is None or citation.score > existing.score:
        citations[key] = citation


def build_citations(
    fact_hits: Iterable[FactHit], context_chunks: Iterable[ContextChunk]
) -> List[Citation]:
    citations_map: dict[tuple[str, str], Citation] = {}

    for hit in fact_hits:
        source = hit.source
        if _is_internal_path(source):
            _upsert_citation(
                citations_map,
                Citation(
                    source=source,
                    chunk_id="fact",
                    score=min(hit.score, 1.0),
                    snippet=_snippet_preview(f"{hit.statement} {hit.values}".strip()),
                ),
            )

    for chunk in context_chunks:
        if _is_internal_path(chunk.source):
            _upsert_citation(
                citations_map,
                Citation(
                    source=chunk.source,
                    chunk_id=chunk.chunk_id,
                    score=min(chunk.score, 1.0),
                    snippet=_snippet_preview(chunk.text),
                )
            )

    citations = sorted(
        citations_map.values(),
        key=lambda citation: (-citation.score, citation.source, citation.chunk_id),
    )
    return citations[:_MAX_CITATIONS]
