from typing import Iterable, List

from app.schemas.query import Citation
from app.services.facts import FactHit
from app.services.retrieval import ContextChunk


def _is_internal_path(path: str) -> bool:
    return not (path.startswith("http://") or path.startswith("https://"))


def build_citations(
    fact_hits: Iterable[FactHit], context_chunks: Iterable[ContextChunk]
) -> List[Citation]:
    citations: List[Citation] = []

    for hit in fact_hits:
        source = hit.source
        if _is_internal_path(source):
            citations.append(Citation(source=source, chunk_id="fact", score=hit.score))

    for chunk in context_chunks:
        if _is_internal_path(chunk.source):
            citations.append(
                Citation(source=chunk.source, chunk_id=chunk.chunk_id, score=chunk.score)
            )

    return citations
