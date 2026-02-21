from __future__ import annotations

import hashlib
from collections import Counter, deque
from threading import Lock
from typing import Deque, Iterable, List, Tuple

from app.services.retrieval import ContextChunk

_WINDOW_SIZE = 200
_history: Deque[str] = deque(maxlen=_WINDOW_SIZE)
_counts: Counter[str] = Counter()
_lock = Lock()


def _stable_key(chunk: ContextChunk) -> str:
    if chunk.chunk_id:
        return chunk.chunk_id
    prefix = chunk.text[:80] if chunk.text else ""
    digest = hashlib.sha1(prefix.encode("utf-8")).hexdigest()
    return f"{chunk.source}::{digest}"


def apply_overuse_penalty(
    chunks: Iterable[ContextChunk], top_score: float | None
) -> Tuple[List[ContextChunk], dict | None]:
    items = list(chunks)
    if not items:
        return items, None

    top_item = max(items, key=lambda item: item.score)
    key = _stable_key(top_item)

    with _lock:
        count = _counts.get(key, 0)
    ratio = count / _WINDOW_SIZE

    score_before = top_item.score
    score_after = score_before
    top_key = key

    effective_top_score = top_score if top_score is not None else 0.0
    if ratio >= 0.20 and effective_top_score < 0.85:
        penalty = 1 - min(0.35, ratio)
        scored = [
            ContextChunk(
                source=item.source,
                chunk_id=item.chunk_id,
                score=item.score * penalty if _stable_key(item) == key else item.score,
                text=item.text,
            )
            for item in items
        ]
        top_after = max(scored, key=lambda item: item.score)
        score_after = top_after.score
        top_key = _stable_key(top_after)
    else:
        scored = items

    with _lock:
        if len(_history) == _WINDOW_SIZE:
            removed = _history[0]
            _counts[removed] -= 1
            if _counts[removed] <= 0:
                del _counts[removed]
        _history.append(top_key)
        _counts[top_key] += 1

    telemetry = {
        "top_key": top_key,
        "ratio": ratio,
        "score_before": score_before,
        "score_after": score_after,
    }
    return scored, telemetry
