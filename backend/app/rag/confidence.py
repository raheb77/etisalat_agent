from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable, Sequence

from app.rag.normalize import normalize_query, normalize_text
from app.schemas.query import Citation
from app.services.facts import FactHit
from app.services.retrieval import ContextChunk

_TOKEN_SPLIT = re.compile(r"\s+")
_QUESTION_FACET_GROUPS = (
    {"مدة", "duration"},
    {"رسوم", "تكلفة", "سعر", "fee", "fees", "cost", "price"},
    {"خطوات", "الخطوات", "مطلوب", "مطلوبة", "required", "step", "steps"},
)
_INSUFFICIENCY_MARKERS = (
    "لا تتضمن",
    "لا تحتوي",
    "لا تشمل",
    "لا توجد معلومات",
    "لا تتوفر معلومات",
    "لا تتوفر ادلة",
    "لا تتوفر أدلة",
    "لم نجد",
    "لم نجد معلومات محددة",
    "الادلة لا تتضمن",
    "الأدلة لا تتضمن",
    "insufficient evidence",
    "no information",
    "evidence does not include",
)
_ASSERTIVE_MARKERS = (
    "سعر",
    "رسوم",
    "تكلفة",
    "مدة",
    "خطوات",
    "مجاني",
    "ريال",
    "دقيقة",
    "ساعة",
    "يتضمن",
    "يتطلب",
    "يشمل",
    "price",
    "cost",
    "duration",
)
_STOPWORDS = {
    "ما",
    "كم",
    "من",
    "في",
    "على",
    "الى",
    "إلى",
    "عن",
    "مع",
    "هل",
    "the",
    "a",
    "an",
    "or",
    "and",
}


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


def _citation_key(citation: Citation) -> str:
    return f"{citation.source}#{citation.chunk_id}"


def _content_tokens(text: str) -> set[str]:
    normalized = normalize_text(text)
    return {
        token
        for token in _TOKEN_SPLIT.split(normalized)
        if token and token not in _STOPWORDS
    }


def _question_numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", normalize_text(text)))


def _evidence_text(
    fact_hits: Sequence[FactHit], contexts: Sequence[ContextChunk]
) -> str:
    parts: list[str] = []
    for fact in fact_hits:
        parts.append(f"{fact.statement} {fact.values}")
    for ctx in contexts[:3]:
        parts.append(ctx.text)
    return " ".join(part for part in parts if part).strip()


def _has_insufficiency_marker(answer: str) -> bool:
    normalized = normalize_text(answer)
    return any(normalize_text(marker) in normalized for marker in _INSUFFICIENCY_MARKERS)


def has_insufficiency_marker(answer: str) -> bool:
    return _has_insufficiency_marker(answer)


def _is_assertive_answer(answer: str) -> bool:
    normalized = normalize_text(answer)
    if not normalized or _has_insufficiency_marker(answer):
        return False
    return any(marker in normalized for marker in _ASSERTIVE_MARKERS) or bool(
        re.search(r"\d", normalized)
    )


def _is_query_highly_transformed(raw_question: str, normalized_question: str) -> bool:
    raw_tokens = _content_tokens(normalize_text(raw_question))
    normalized_tokens = _content_tokens(normalized_question)
    if not raw_tokens or not normalized_tokens:
        return False
    if raw_tokens == normalized_tokens:
        return False
    overlap = len(raw_tokens & normalized_tokens) / max(1, len(raw_tokens | normalized_tokens))
    return overlap < 0.65


def detect_answer_evidence_issue(
    raw_question: str,
    normalized_question: str,
    answer: str,
    fact_hits: Sequence[FactHit],
    contexts: Sequence[ContextChunk],
    citations: Sequence[Citation],
    top_score: float | None,
) -> tuple[bool, str]:
    evidence_text = _evidence_text(fact_hits, contexts)
    normalized_question_text = normalize_text(normalized_question or raw_question)
    normalized_evidence_text = normalize_text(evidence_text)
    normalized_answer_text = normalize_text(answer)
    strong_matching_evidence = _normalize_score(top_score) >= 0.70 and len(citations) >= 1

    # Guard only in deterministic contradiction/insufficiency cases:
    # 1) the answer claims no evidence/information while strong evidence exists
    # 2) the question asks for a specific facet (for example steps/requirements) that
    #    is not present in either the retrieved evidence or the answer.
    if strong_matching_evidence and _has_insufficiency_marker(answer):
        return True, "insufficient_answer_with_strong_evidence"

    question_facet_groups = [
        facet_group
        for facet_group in _QUESTION_FACET_GROUPS
        if any(facet in normalized_question_text for facet in facet_group)
    ]
    if question_facet_groups and not all(
        any(
            facet in normalized_evidence_text or facet in normalized_answer_text
            for facet in facet_group
        )
        for facet_group in question_facet_groups
    ):
        return True, "unsupported_request_facet"

    return False, ""


def calibrate_answer_confidence(
    base_confidence: int,
    top_score: float | None,
    citations: Sequence[Citation],
    answer: str,
    category: str,
    raw_question: str,
    normalized_question: str,
    fact_hits: Sequence[FactHit],
    contexts: Sequence[ContextChunk],
) -> tuple[int, str]:
    score = _normalize_score(top_score)
    confidence = base_confidence
    if not citations:
        return 20, "no_citations"

    # If the answer itself is phrased as insufficient evidence, do not keep a
    # high-confidence score. Strong contradiction is already handled earlier by
    # the deterministic guard; this caps the remaining non-guarded cases.
    if _has_insufficiency_marker(answer):
        return min(confidence, 35), "insufficiency_answer"

    citation_keys = [_citation_key(citation) for citation in citations]
    unique_citations = len(set(citation_keys))
    duplicate_citations = unique_citations < len(citation_keys)
    evidence_text = _evidence_text(fact_hits, contexts)
    evidence_bundle = normalize_text(f"{evidence_text} {answer}")
    reason = ""

    if 0.50 <= score < 0.70:
        confidence = min(confidence, 50)
        reason = reason or "borderline_evidence"

    if unique_citations <= 1 and score < 0.85:
        confidence = min(confidence, 60)
        reason = reason or "weak_evidence_count"

    if duplicate_citations:
        confidence = min(confidence, 60)
        reason = reason or "duplicated_evidence"

    if category == "unknown" and _is_assertive_answer(answer):
        confidence = min(confidence, 35)
        reason = reason or "unknown_category_assertive_answer"

    if _is_query_highly_transformed(raw_question, normalized_question):
        confidence = min(confidence, 50)
        reason = reason or "high_query_transformation"

    question_numbers = _question_numbers(raw_question)
    if question_numbers and any(number not in evidence_bundle for number in question_numbers):
        confidence = min(confidence, 35)
        reason = reason or "unsupported_question_number"

    if Counter(citation_keys).most_common(1) and Counter(citation_keys).most_common(1)[0][1] > 1:
        confidence = min(confidence, 60)
        reason = reason or "duplicated_evidence"

    return max(20, confidence), reason
