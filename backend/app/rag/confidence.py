from __future__ import annotations

import math


def _normalize_score(score: float | None) -> float:
    if score is None:
        return 0.0
    if isinstance(score, float) and math.isnan(score):
        return 0.0
    return float(score)


def calculate_confidence(
    top_score: float | None,
    citations_count: int,
    did_fallback: bool,
    intent: str,
) -> int:
    score = _normalize_score(top_score)
    if did_fallback:
        return 20

    if score >= 0.85:
        return 85
    if score >= 0.70:
        return 75
    if score >= 0.50:
        return 60
    return 20
