from __future__ import annotations

import re
from typing import Iterable, Tuple

_AR_KEYWORDS: Iterable[str] = (
    "أفضل هاتف",
    "جوال",
    "آيفون",
    "سامسونج",
    "لابتوب",
    "سيارة",
    "بيتكوين",
    "وصفة",
    "مرض",
)

_EN_KEYWORDS: Iterable[str] = (
    "best phone",
    "iphone",
    "samsung",
    "laptop",
    "car",
    "bitcoin",
    "recipe",
    "diagnosis",
)

_AR_COMPARE = re.compile(r"(قارن|مقارنة)\s+")
_EN_COMPARE = re.compile(r"\b(vs|compare)\b", re.IGNORECASE)

_AR_PATTERNS = [
    re.compile(r"(أفضل|افضل|احسن|أحسن)\s*(هاتف|جوال|تلفون|موبايل|جهاز)"),
    re.compile(r"(قارن|مقارنة|مقارنه)\s*(بين)?\s*(ايفون|آيفون|سامسونج|هواوي|بيكسل)"),
    re.compile(r"(سعر|اسعار)\s*(ايفون|آيفون|سامسونج|هواوي|بيكسل)"),
]
_EN_PATTERNS = [
    re.compile(r"\bbest\s+phone\b", re.IGNORECASE),
    re.compile(r"\biphone\s+vs\b", re.IGNORECASE),
    re.compile(r"\bcompare\s+phones\b", re.IGNORECASE),
]


def _keyword_score(query: str, keywords: Iterable[str]) -> float:
    matches = [kw for kw in keywords if kw in query]
    if not matches:
        return 0.0
    return min(1.0, 0.6 + 0.1 * len(matches))


def _comparison_score(query: str) -> float:
    if _AR_COMPARE.search(query) or _EN_COMPARE.search(query):
        return 0.2
    return 0.0


def is_out_of_scope(query: str) -> Tuple[bool, float, str | None]:
    normalized = query.strip().lower()
    if not normalized:
        return False, 0.0, None

    if any(pattern.search(normalized) for pattern in _AR_PATTERNS + _EN_PATTERNS):
        return True, 0.95, "keyword_oos"

    score = 0.0
    score = max(score, _keyword_score(normalized, _AR_KEYWORDS))
    score = max(score, _keyword_score(normalized, _EN_KEYWORDS))
    score = min(1.0, score + _comparison_score(normalized))

    if score >= 0.75:
        return True, score, "keyword_match"

    return False, score, None
