from __future__ import annotations

from typing import Tuple


def should_fallback(
    citations_count: int, top_score: float, intent_primary: str
) -> Tuple[bool, str | None]:
    if citations_count == 0:
        return True, "no_citations"
    if intent_primary != "general" and top_score < 0.45:
        return True, "low_score_for_intent"
    if top_score < 0.35:
        return True, "low_top_score"
    return False, None
