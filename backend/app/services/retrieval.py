from dataclasses import dataclass
from typing import List


@dataclass
class ContextChunk:
    source: str
    chunk_id: str
    score: float
    text: str


def retrieve_context(question: str, category: str) -> List[ContextChunk]:
    # TODO: integrate Qdrant or other vector store in Phase 2
    return []
