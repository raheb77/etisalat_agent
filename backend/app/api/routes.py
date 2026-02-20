import hashlib
import json
import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core import citations, confidence as confidence_svc, policy, router, sanitizer
from app.rag.ambiguity import detect_ambiguity
from app.rag.intent import detect_intent
from app.rag.oos import is_out_of_scope
from app.rag.overuse import apply_overuse_penalty
from app.rag.confidence import calculate_confidence
from app.rag.relevance import should_fallback
from app.schemas.query import QueryRequest, QueryResponse
from app.services import audit, facts, llm, retrieval
from app.services.decision_result import DecisionResult
from app.services.query_cache import NEGATIVE_CACHE, POSITIVE_CACHE, build_cache_key
from app.telemetry.cost import estimate_cost_usd, estimate_tokens
from app.telemetry.metrics import inc_counter, observe_ms, snapshot
from app.telemetry.timing import StageTimer

router_api = APIRouter()
telemetry_logger = logging.getLogger("app.telemetry")

_CACHE_TELEMETRY_KEYS = [
    "is_ambiguous",
    "ambiguity_score",
    "ambiguity_reason_code",
    "detected_intent",
    "secondary_intents",
    "intent_score",
    "citations_count",
    "top_score",
    "top_score_before",
    "top_score_after",
    "top_source_preview",
    "top_key",
    "did_fallback",
    "fallback_reason",
    "fallback_reason_code",
    "cache_key_hash",
    "cache_hit",
    "neg_cache_hit",
    "is_oos",
    "oos_score",
    "gate_score_used",
]

def _reason_code(raw_reason: str | None) -> str:
    if not raw_reason:
        return ""
    lowered = raw_reason.strip().lower()
    mapping = {
        "high risk category": "high_risk_category",
        "policy restriction": "policy_handoff_override",
        "low confidence": "low_confidence",
        "out of scope": "keyword_oos",
        "insufficient knowledge evidence": "low_confidence",
    }
    return mapping.get(lowered, raw_reason.strip())


def localize_reason(reason_code: str, locale: str) -> str:
    code = (reason_code or "").strip()
    if not code:
        return ""
    if locale == "ar-SA":
        mapping = {
            "low_confidence": "أدلة ضعيفة",
            "high_risk_category": "تصعيد بسبب حساسية الطلب",
            "policy_handoff_override": "يتطلب تصعيد",
            "keyword_oos": "خارج النطاق",
            "oos_score_gate": "خارج النطاق",
            "no_citations": "لا توجد مصادر",
            "low_top_score": "أدلة ضعيفة",
            "low_score_for_intent": "أدلة غير كافية",
            "vague_short_query": "يرجى التوضيح",
            "internal_error": "خطأ داخلي",
            "retrieval_error": "تعذر الاسترجاع",
            "ranking_error": "تعذر ترتيب النتائج",
            "answer_error": "تعذر توليد الإجابة",
        }
        return mapping.get(code, "يتطلب مراجعة")
    mapping = {
        "low_confidence": "Low evidence",
        "high_risk_category": "High risk category",
        "policy_handoff_override": "Escalation required",
        "keyword_oos": "Out of scope",
        "oos_score_gate": "Out of scope",
        "no_citations": "No sources",
        "low_top_score": "Low evidence",
        "low_score_for_intent": "Insufficient evidence",
        "vague_short_query": "Clarification required",
        "internal_error": "Internal error",
        "retrieval_error": "Retrieval error",
        "ranking_error": "Ranking error",
        "answer_error": "Answer error",
    }
    return mapping.get(code, code)


def _relevance_fallback_payload(locale: str) -> tuple[str, list[str]]:
    if locale == "ar-SA":
        return (
            "لم نجد معلومات محددة للإجابة على هذا السؤال. الرجاء توضيح الطلب أو تزويدنا بتفاصيل أكثر.",
            ["اذكر رقم الخدمة أو نوع الباقة إن وجد.", "حدد المشكلة أو الموقع بدقة أكبر."],
        )
    return (
        "We couldn't find specific information to answer this. Please clarify your request or share more details.",
        ["Mention the service or plan, if applicable.", "Clarify the issue or location."],
    )


def _cap_score(score: float | None) -> float | None:
    if score is None:
        return None
    return min(float(score), 1.0)


def _ms_nonzero(value_ms: int) -> int:
    return value_ms if value_ms > 0 else 1


@router_api.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router_api.get("/metrics")
def metrics() -> JSONResponse:
    data = snapshot()
    counters = data.get("counters", {})
    latency = data.get("latency_ms", {})
    ordered = {
        "counters": {k: counters[k] for k in sorted(counters)},
        "latency_ms": {k: latency[k] for k in sorted(latency)},
    }
    return JSONResponse(content=ordered)


@router_api.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, http_request: Request) -> QueryResponse:
    request_id = uuid.uuid4().hex
    start_time = time.perf_counter()
    decision_path: list[str] = []
    timings: dict = {
        "intent": 0,
        "retrieve": 0,
        "rank": 0,
        "answer": 0,
        "fallback": 0,
        "cache_hit": 0,
        "total": 0,
        "skipped": False,
    }
    telemetry: dict = {
        "request_id": request_id,
        "locale": request.locale,
        "channel": request.channel,
        "category_hint_present": bool(request.category_hint),
        "query_len": None,
        "query_preview": None,
        "is_oos": False,
        "oos_score": None,
        "is_ambiguous": False,
        "detected_intent": "unknown",
        "secondary_intents": [],
        "intent_score": None,
        "citations_count": 0,
        "top_score": None,
        "top_score_before": 0.0,
        "top_score_after": 0.0,
        "gate_score_used": 0.0,
        "top_source_preview": None,
        "top_key": None,
        "did_fallback": False,
        "fallback_reason": "",
        "fallback_reason_code": "",
        "confidence": None,
        "handoff": None,
        "handoff_reason": "",
        "latency_ms": None,
        "decision_path": decision_path,
        "timings_ms": timings,
        "tokens_in_est": 0,
        "tokens_out_est": 0,
        "cost_usd_est": 0.0,
        "cache_hit": False,
        "neg_cache_hit": False,
        "served_from_cache": False,
        "cache_key_hash": "",
        "rate_limited": False,
        "error_stage": "",
        "error_type": "",
        "error_message_preview": "",
    }
    error_message = None
    masked_question, has_pii, pii_types = sanitizer.sanitize_question(request.question)
    telemetry["query_len"] = len(masked_question)
    telemetry["query_preview"] = masked_question.replace("\n", " ")[:80]
    tokens_in_est = estimate_tokens(masked_question)
    telemetry["tokens_in_est"] = tokens_in_est
    cache_key = build_cache_key(masked_question, request.locale, request.channel)
    cache_key_hash = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()[:10]
    telemetry["cache_key_hash"] = cache_key_hash

    user_id = http_request.headers.get("X-User-ID", "unknown")
    try:
        inc_counter(
            "query_requests_total",
            {"channel": request.channel, "locale": request.locale},
        )
        cache_entry = POSITIVE_CACHE.get(cache_key)
        if cache_entry:
            telemetry["cache_hit"] = True
            telemetry["served_from_cache"] = True
            inc_counter("query_cache_hit_total")
            cached_result = DecisionResult.from_cache(cache_entry)
            if cached_result.telemetry:
                telemetry.update(cached_result.telemetry)
            if cached_result.decision_path:
                decision_path[:] = cached_result.decision_path
            timings["skipped"] = True
            response_payload = dict(cached_result.response or {})
            telemetry["cache_hit"] = True
            telemetry["served_from_cache"] = True
            telemetry["did_fallback"] = bool(telemetry.get("did_fallback", False))
            telemetry["query_len"] = len(masked_question)
            telemetry["query_preview"] = masked_question.replace("\n", " ")[:80]
            telemetry["tokens_in_est"] = tokens_in_est
            telemetry["cache_key_hash"] = cache_key_hash
            telemetry["fallback_reason_code"] = telemetry.get(
                "fallback_reason_code", telemetry.get("fallback_reason", "")
            )
            if not telemetry.get("detected_intent"):
                telemetry["detected_intent"] = "unknown"
            confidence_value = response_payload.get("confidence", 0.0)
            try:
                confidence_value = float(confidence_value)
            except (TypeError, ValueError):
                confidence_value = 0.0
            confidence_value = min(1.0, max(0.0, confidence_value))
            handoff = bool(response_payload.get("handoff", False))
            handoff_reason = response_payload.get("handoff_reason", "")
            if not handoff:
                handoff_reason = ""
            response_payload.update(
                {
                    "confidence": confidence_value,
                    "handoff": handoff,
                    "handoff_reason": handoff_reason,
                }
            )
            telemetry["confidence"] = int(round(confidence_value * 100))
            telemetry["handoff"] = handoff
            telemetry["handoff_reason"] = handoff_reason
            telemetry["citations_count"] = len(response_payload.get("citations", []) or [])
            answer = str(response_payload.get("answer", ""))
            tokens_out_est = estimate_tokens(answer)
            telemetry["tokens_out_est"] = tokens_out_est
            telemetry["cost_usd_est"] = estimate_cost_usd(tokens_in_est, tokens_out_est)
            inc_counter("query_tokens_out_total", value=tokens_out_est)
            telemetry["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            timings["cache_hit"] = _ms_nonzero(telemetry["latency_ms"])
            observe_ms(
                "query_stage_ms",
                timings["cache_hit"],
                {"channel": request.channel, "stage": "cache_hit"},
            )
            timings["total"] = _ms_nonzero(telemetry["latency_ms"])
            return QueryResponse(
                **response_payload,
                debug={"decision_path": decision_path}
                if http_request.headers.get("X-Debug") == "1"
                else None,
            )
        neg_cache_entry = NEGATIVE_CACHE.get(cache_key)
        if neg_cache_entry:
            telemetry["cache_hit"] = True
            telemetry["neg_cache_hit"] = True
            telemetry["served_from_cache"] = True
            inc_counter("query_cache_hit_total")
            inc_counter("negative_cache_hit_total")
            cached_result = DecisionResult.from_cache(neg_cache_entry)
            if cached_result.telemetry:
                telemetry.update(cached_result.telemetry)
            if cached_result.decision_path:
                decision_path[:] = cached_result.decision_path
            timings["skipped"] = True
            response_payload = dict(cached_result.response or {})
            telemetry["cache_hit"] = True
            telemetry["neg_cache_hit"] = True
            telemetry["served_from_cache"] = True
            telemetry["did_fallback"] = True
            telemetry["query_len"] = len(masked_question)
            telemetry["query_preview"] = masked_question.replace("\n", " ")[:80]
            telemetry["tokens_in_est"] = tokens_in_est
            telemetry["cache_key_hash"] = cache_key_hash
            telemetry["fallback_reason_code"] = telemetry.get(
                "fallback_reason_code", telemetry.get("fallback_reason", "")
            )
            if not telemetry.get("detected_intent"):
                telemetry["detected_intent"] = "unknown"
            answer = str(response_payload.get("answer", ""))
            tokens_out_est = estimate_tokens(answer)
            telemetry["tokens_out_est"] = tokens_out_est
            telemetry["cost_usd_est"] = estimate_cost_usd(tokens_in_est, tokens_out_est)
            inc_counter("query_tokens_out_total", value=tokens_out_est)
            telemetry["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            timings["cache_hit"] = _ms_nonzero(telemetry["latency_ms"])
            observe_ms(
                "query_stage_ms",
                timings["cache_hit"],
                {"channel": request.channel, "stage": "cache_hit"},
            )
            timings["total"] = _ms_nonzero(telemetry["latency_ms"])
            return QueryResponse(
                **response_payload,
                debug={"decision_path": decision_path}
                if http_request.headers.get("X-Debug") == "1"
                else None,
            )
        inc_counter("query_cache_miss_total")
        inc_counter("query_tokens_in_total", value=tokens_in_est)
        is_oos, oos_score, oos_reason = is_out_of_scope(masked_question)
        telemetry["is_oos"] = is_oos
        telemetry["oos_score"] = oos_score
        if is_oos or oos_score >= 0.65:
            reason_code = oos_reason or "oos_score_gate"
            decision_path.append(f"oos:{reason_code}")
            if is_oos:
                inc_counter("query_oos_total")
            inc_counter("query_fallback_total", {"fallback_reason_code": reason_code})
            inc_counter("query_handoff_total", {"handoff_reason_code": reason_code})
            telemetry["did_fallback"] = True
            telemetry["fallback_reason"] = reason_code
            telemetry["citations_count"] = 0
            telemetry["top_score"] = None
            telemetry["top_source_preview"] = None
            telemetry["top_key"] = None
            telemetry["confidence"] = 20
            telemetry["handoff"] = True
            telemetry["handoff_reason"] = reason_code
            telemetry["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            timings["fallback"] = _ms_nonzero(1)
            observe_ms(
                "query_stage_ms",
                timings["fallback"],
                {"channel": request.channel, "stage": "fallback"},
            )
            response_handoff_reason = localize_reason(reason_code, request.locale)

            answer = (
                "خارج نطاق مساعد الاتصالات. الرجاء طرح سؤال متعلق بالخدمات أو الخطط أو التغطية."
                if request.locale == "ar-SA"
                else "Out of scope. Please ask about telecom services, plans, or coverage."
            )
            steps = (
                ["اذكر الخدمة أو الخطة المطلوبة.", "حدد المشكلة أو المكان بوضوح."]
                if request.locale == "ar-SA"
                else ["Mention the service or plan.", "Specify the issue or location."]
            )
            tokens_out_est = estimate_tokens(answer)
            telemetry["tokens_out_est"] = tokens_out_est
            telemetry["cost_usd_est"] = estimate_cost_usd(tokens_in_est, tokens_out_est)
            inc_counter("query_tokens_out_total", value=tokens_out_est)

            return QueryResponse(
                answer=answer,
                steps=steps,
                citations=[],
                confidence=0.2,
                category="unknown",
                risk_level="low",
                handoff=True,
                handoff_reason=response_handoff_reason,
                handoff_payload=None,
                debug={"decision_path": decision_path}
                if http_request.headers.get("X-Debug") == "1"
                else None,
            )

        is_ambiguous, ambiguity_score, ambiguity_reason = detect_ambiguity(
            masked_question
        )
        telemetry["is_ambiguous"] = is_ambiguous
        telemetry["ambiguity_score"] = ambiguity_score
        telemetry["ambiguity_reason_code"] = ambiguity_reason
        if is_ambiguous:
            reason_code = ambiguity_reason or "vague_short_query"
            decision_path.append(f"ambiguous:{reason_code}")
            inc_counter("query_ambiguous_total")
            telemetry["citations_count"] = 0
            telemetry["confidence"] = 50
            telemetry["handoff"] = False
            telemetry["handoff_reason"] = ""
            telemetry["fallback_reason_code"] = reason_code
            telemetry["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            answer = (
                "سؤالك غير واضح. للتوضيح: هل تقصد مشكلة في (الفاتورة) أو (الباقة) أو (الشبكة)؟ اذكر تفاصيل أكثر."
                if request.locale == "ar-SA"
                else "Your request is unclear. Is it about billing, plans, or network? Please add details."
            )
            steps = (
                [
                    "حدد نوع الخدمة المطلوبة (فاتورة، باقة، شبكة).",
                    "اذكر تفاصيل مثل الرقم أو الموقع أو نوع الباقة.",
                ]
                if request.locale == "ar-SA"
                else [
                    "Specify the service (billing, plans, network).",
                    "Add details like number, location, or plan name.",
                ]
            )
            tokens_out_est = estimate_tokens(answer)
            telemetry["tokens_out_est"] = tokens_out_est
            telemetry["cost_usd_est"] = estimate_cost_usd(tokens_in_est, tokens_out_est)
            inc_counter("query_tokens_out_total", value=tokens_out_est)
            if reason_code == "vague_short_query":
                telemetry_snapshot = {
                    key: telemetry.get(key) for key in _CACHE_TELEMETRY_KEYS
                }
                telemetry_snapshot["did_fallback"] = True
                telemetry_snapshot["fallback_reason_code"] = reason_code
                telemetry_snapshot["fallback_reason"] = reason_code
                decision_result = DecisionResult(
                    response={
                        "answer": answer,
                        "steps": steps,
                        "citations": [],
                        "confidence": 0.5,
                        "category": "unknown",
                        "risk_level": "low",
                        "handoff": False,
                        "handoff_reason": "",
                        "handoff_payload": None,
                    },
                    telemetry=telemetry_snapshot,
                    decision_path=decision_path[:],
                )
                NEGATIVE_CACHE.set(cache_key, decision_result.to_cache())
                inc_counter("negative_cache_store_total")
            return QueryResponse(
                answer=answer,
                steps=steps,
                citations=[],
                confidence=0.5,
                category="unknown",
                risk_level="low",
                handoff=False,
                handoff_reason="",
                handoff_payload=None,
                debug={"decision_path": decision_path}
                if http_request.headers.get("X-Debug") == "1"
                else None,
            )

        with StageTimer() as intent_timer:
            intent_result = detect_intent(masked_question)
        timings["intent"] = _ms_nonzero(intent_timer.duration_ms)
        observe_ms(
            "query_stage_ms",
            timings["intent"],
            {"channel": request.channel, "stage": "intent"},
        )
        decision_path.append(f"intent:{intent_result.primary}")
        telemetry["detected_intent"] = intent_result.primary
        telemetry["secondary_intents"] = intent_result.secondary
        telemetry["intent_score"] = intent_result.score

        category, risk = router.route(masked_question, request.category_hint)
        if not telemetry["detected_intent"] or telemetry["detected_intent"] == "unknown":
            telemetry["detected_intent"] = category

        try:
            with StageTimer() as retrieve_timer:
                fact_hits = facts.search_facts(masked_question, category)
                decision_path.append("retrieve")
                ctx = retrieval.retrieve_context(masked_question, category)
            timings["retrieve"] = _ms_nonzero(retrieve_timer.duration_ms)
            observe_ms(
                "query_stage_ms",
                timings["retrieve"],
                {"channel": request.channel, "stage": "retrieve"},
            )
        except Exception as exc:
            reason_code = "retrieval_error"
            decision_path.append(f"fallback:{reason_code}")
            telemetry["did_fallback"] = True
            telemetry["fallback_reason"] = reason_code
            telemetry["fallback_reason_code"] = reason_code
            telemetry["citations_count"] = 0
            telemetry["confidence"] = 20
            telemetry["handoff"] = True
            telemetry["handoff_reason"] = reason_code
            telemetry["error_stage"] = "retrieval"
            telemetry["error_type"] = type(exc).__name__
            telemetry["error_message_preview"] = str(exc)[:200]
            inc_counter("query_fallback_total", {"fallback_reason_code": reason_code})
            inc_counter("query_handoff_total", {"handoff_reason_code": reason_code})
            answer = "تعذر إكمال الطلب حالياً، يرجى المحاولة لاحقاً أو التواصل مع الدعم."
            timings["fallback"] = _ms_nonzero(1)
            observe_ms(
                "query_stage_ms",
                timings["fallback"],
                {"channel": request.channel, "stage": "fallback"},
            )
            tokens_out_est = estimate_tokens(answer)
            telemetry["tokens_out_est"] = tokens_out_est
            telemetry["cost_usd_est"] = estimate_cost_usd(tokens_in_est, tokens_out_est)
            inc_counter("query_tokens_out_total", value=tokens_out_est)
            telemetry["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            return QueryResponse(
                answer=answer,
                steps=[],
                citations=[],
                confidence=0.2,
                category="unknown",
                risk_level="low",
                handoff=True,
                handoff_reason=localize_reason(reason_code, request.locale),
                handoff_payload=None,
                debug={"decision_path": decision_path}
                if http_request.headers.get("X-Debug") == "1"
                else None,
            )
        try:
            with StageTimer() as rank_timer:
                raw_top_score_before = max([c.score for c in ctx], default=None)
                ctx, overuse_meta = apply_overuse_penalty(ctx, raw_top_score_before)
                cits = citations.build_citations(fact_hits, ctx)
                decision_path.append("rank")
                raw_top_score_after = max([c.score for c in ctx], default=None)
            timings["rank"] = _ms_nonzero(rank_timer.duration_ms)
            observe_ms(
                "query_stage_ms",
                timings["rank"],
                {"channel": request.channel, "stage": "rank"},
            )
        except Exception as exc:
            reason_code = "ranking_error"
            decision_path.append(f"fallback:{reason_code}")
            telemetry["did_fallback"] = True
            telemetry["fallback_reason"] = reason_code
            telemetry["fallback_reason_code"] = reason_code
            telemetry["citations_count"] = 0
            telemetry["confidence"] = 20
            telemetry["handoff"] = True
            telemetry["handoff_reason"] = reason_code
            telemetry["error_stage"] = "ranking"
            telemetry["error_type"] = type(exc).__name__
            telemetry["error_message_preview"] = str(exc)[:200]
            inc_counter("query_fallback_total", {"fallback_reason_code": reason_code})
            inc_counter("query_handoff_total", {"handoff_reason_code": reason_code})
            answer = "تعذر إكمال الطلب حالياً، يرجى المحاولة لاحقاً أو التواصل مع الدعم."
            timings["fallback"] = _ms_nonzero(1)
            observe_ms(
                "query_stage_ms",
                timings["fallback"],
                {"channel": request.channel, "stage": "fallback"},
            )
            tokens_out_est = estimate_tokens(answer)
            telemetry["tokens_out_est"] = tokens_out_est
            telemetry["cost_usd_est"] = estimate_cost_usd(tokens_in_est, tokens_out_est)
            inc_counter("query_tokens_out_total", value=tokens_out_est)
            telemetry["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            return QueryResponse(
                answer=answer,
                steps=[],
                citations=[],
                confidence=0.2,
                category="unknown",
                risk_level="low",
                handoff=True,
                handoff_reason=localize_reason(reason_code, request.locale),
                handoff_payload=None,
                debug={"decision_path": decision_path}
                if http_request.headers.get("X-Debug") == "1"
                else None,
            )
        top_score_before = _cap_score(raw_top_score_before)
        top_score_after = _cap_score(raw_top_score_after)
        # before: raw retrieval top score; after: post-penalty; used: score for gating.
        telemetry["top_score_before"] = (
            top_score_before if top_score_before is not None else 0.0
        )
        telemetry["top_score_after"] = (
            top_score_after if top_score_after is not None else 0.0
        )
        telemetry["citations_count"] = len(cits)
        top_score = None
        if cits:
            top = max(cits, key=lambda item: item.score)
            top_score = _cap_score(top.score)
            telemetry["top_score"] = top_score
            telemetry["top_source_preview"] = top.source[:60]
            telemetry["top_key"] = f"{top.source}#{top.chunk_id}"
        gate_score_used = (
            top_score_after
            if top_score_after is not None
            else (top_score if top_score is not None else 0.0)
        )
        telemetry["gate_score_used"] = gate_score_used
        if overuse_meta:
            telemetry["overuse"] = {
                "top_key": overuse_meta["top_key"],
                "ratio": overuse_meta["ratio"],
                "score_before": _cap_score(overuse_meta["score_before"]),
                "score_after": _cap_score(overuse_meta["score_after"]),
            }

        fallback_needed, fallback_reason = should_fallback(
            citations_count=len(cits),
            top_score=gate_score_used,
            intent_primary=intent_result.primary,
        )
        if fallback_needed:
            reason_code = fallback_reason or "low_confidence"
            decision_path.append(f"fallback:{reason_code}")
            inc_counter("query_fallback_total", {"fallback_reason_code": reason_code})
            inc_counter("query_handoff_total", {"handoff_reason_code": reason_code})
            telemetry["did_fallback"] = True
            telemetry["fallback_reason"] = reason_code
            telemetry["fallback_reason_code"] = reason_code
            telemetry["confidence"] = 20
            telemetry["handoff"] = True
            telemetry["handoff_reason"] = reason_code
            telemetry["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            with StageTimer() as fallback_timer:
                answer, steps = _relevance_fallback_payload(request.locale)
            timings["fallback"] = _ms_nonzero(fallback_timer.duration_ms)
            observe_ms(
                "query_stage_ms",
                timings["fallback"],
                {"channel": request.channel, "stage": "fallback"},
            )
            response_handoff_reason = localize_reason(reason_code, request.locale)
            tokens_out_est = estimate_tokens(answer)
            telemetry["tokens_out_est"] = tokens_out_est
            telemetry["cost_usd_est"] = estimate_cost_usd(tokens_in_est, tokens_out_est)
            inc_counter("query_tokens_out_total", value=tokens_out_est)

            response_payload = {
                "answer": answer,
                "steps": steps,
                "citations": [],
                "confidence": 0.2,
                "category": category,
                "risk_level": risk,
                "handoff": True,
                "handoff_reason": response_handoff_reason,
                "handoff_payload": None,
            }
            if reason_code == "no_citations":
                telemetry["fallback_reason_code"] = reason_code
                telemetry_snapshot = {
                    key: telemetry.get(key) for key in _CACHE_TELEMETRY_KEYS
                }
                decision_result = DecisionResult(
                    response=response_payload,
                    telemetry=telemetry_snapshot,
                    decision_path=decision_path[:],
                )
                NEGATIVE_CACHE.set(cache_key, decision_result.to_cache())
                inc_counter("negative_cache_store_total")
            return QueryResponse(
                **response_payload,
                debug={"decision_path": decision_path}
                if http_request.headers.get("X-Debug") == "1"
                else None,
            )

        # Confidence + handoff path:
        # 1) Use core confidence for policy signal.
        # 2) Use gate_score_used for final confidence tiers.
        # 3) Apply policy override (fraud/high-risk), then enforce invariants.
        retrieval_score = gate_score_used if gate_score_used is not None else 0.0
        conf = confidence_svc.compute_confidence(
            fact_hits_count=len(fact_hits),
            retrieval_score=retrieval_score,
            conflict_detected=False,
            risk_level=risk,
        )
        telemetry["intent_score"] = conf
        calibrated_confidence = calculate_confidence(
            top_score=gate_score_used,
            citations_count=len(cits),
            did_fallback=False,
            intent=intent_result.primary,
        )

        decision = policy.policy_decision(
            category, risk, conf, bool(fact_hits) or bool(ctx)
        )
        handoff = decision["handoff"]
        reason_code = _reason_code(decision["handoff_reason"] if decision["handoff"] else "")
        override_active = False
        if intent_result.primary == "fraud":
            override_active = True
            handoff = True
            reason_code = "high_risk_category"
        elif category in {"fraud", "legal", "security"} or risk == "high":
            override_active = True
            handoff = True
            reason_code = reason_code or "high_risk_category"

        if not override_active:
            if calibrated_confidence >= 60:
                handoff = False
                reason_code = ""
            elif calibrated_confidence < 50:
                handoff = True
                reason_code = "low_confidence"
            if not handoff and calibrated_confidence < 50:
                calibrated_confidence = 50
        telemetry["confidence"] = calibrated_confidence
        telemetry["handoff"] = handoff
        telemetry["handoff_reason"] = reason_code
        response_handoff_reason = localize_reason(reason_code, request.locale)
        if handoff:
            inc_counter("query_handoff_total", {"handoff_reason_code": reason_code or "unknown"})

        try:
            with StageTimer() as answer_timer:
                answer, steps = llm.generate_answer(
                    masked_question, fact_hits, ctx, request.locale
                )
            timings["answer"] = _ms_nonzero(answer_timer.duration_ms)
            observe_ms(
                "query_stage_ms",
                timings["answer"],
                {"channel": request.channel, "stage": "answer"},
            )
        except Exception as exc:
            reason_code = "answer_error"
            decision_path.append(f"fallback:{reason_code}")
            telemetry["did_fallback"] = True
            telemetry["fallback_reason"] = reason_code
            telemetry["fallback_reason_code"] = reason_code
            telemetry["citations_count"] = 0
            telemetry["confidence"] = 20
            telemetry["handoff"] = True
            telemetry["handoff_reason"] = reason_code
            telemetry["error_stage"] = "answer"
            telemetry["error_type"] = type(exc).__name__
            telemetry["error_message_preview"] = str(exc)[:200]
            inc_counter("query_fallback_total", {"fallback_reason_code": reason_code})
            inc_counter("query_handoff_total", {"handoff_reason_code": reason_code})
            answer = "تعذر إكمال الطلب حالياً، يرجى المحاولة لاحقاً أو التواصل مع الدعم."
            timings["fallback"] = _ms_nonzero(1)
            observe_ms(
                "query_stage_ms",
                timings["fallback"],
                {"channel": request.channel, "stage": "fallback"},
            )
            tokens_out_est = estimate_tokens(answer)
            telemetry["tokens_out_est"] = tokens_out_est
            telemetry["cost_usd_est"] = estimate_cost_usd(tokens_in_est, tokens_out_est)
            inc_counter("query_tokens_out_total", value=tokens_out_est)
            telemetry["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            return QueryResponse(
                answer=answer,
                steps=[],
                citations=[],
                confidence=0.2,
                category="unknown",
                risk_level="low",
                handoff=True,
                handoff_reason=localize_reason(reason_code, request.locale),
                handoff_payload=None,
                debug={"decision_path": decision_path}
                if http_request.headers.get("X-Debug") == "1"
                else None,
            )
        decision_path.append("answer")
        if handoff and category in {"legal", "fraud", "security"}:
            answer = "لا يمكن معالجة هذا الطلب هنا. سيتم تحويله إلى الجهة المختصة."
            telemetry["did_fallback"] = True
            telemetry["fallback_reason"] = "policy_handoff_override"
            inc_counter("query_fallback_total", {"fallback_reason_code": "policy_handoff_override"})
            if not any(item.startswith("fallback:") for item in decision_path):
                decision_path.append("fallback:policy_handoff_override")
        if not any(item.startswith(("oos:", "ambiguous:", "fallback:")) for item in decision_path):
            decision_path.append("normal")
        tokens_out_est = estimate_tokens(answer)
        telemetry["tokens_out_est"] = tokens_out_est
        telemetry["cost_usd_est"] = estimate_cost_usd(tokens_in_est, tokens_out_est)
        inc_counter("query_tokens_out_total", value=tokens_out_est)

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        telemetry["latency_ms"] = latency_ms
        audit.log_event(
            {
                "user_id": user_id,
                "category": category,
                "risk_level": risk,
                "confidence": conf,
                "handoff": decision["handoff"],
                "latency_ms": latency_ms,
                "pii_detected": has_pii,
                "sanitized_question": masked_question,
            }
        )

        evidence_items = []
        if decision["handoff"]:
            for hit in fact_hits[:4]:
                evidence_items.append(f"{hit.source}#fact")
            if not evidence_items:
                for chunk in ctx[:4]:
                    evidence_items.append(f"{chunk.source}#{chunk.chunk_id}")
            evidence_items = evidence_items[:4]

        response_payload = {
            "answer": answer,
            "steps": steps,
            "citations": cits,
            "confidence": calibrated_confidence / 100.0,
            "category": category,
            "risk_level": risk,
            "handoff": handoff,
            "handoff_reason": response_handoff_reason if handoff else "",
            "handoff_payload": {
                "team": decision["team"],
                "summary": f"ملخص السؤال: {masked_question}",
                "evidence": evidence_items if evidence_items else [f"{category}#no_evidence"],
            } if handoff else None,
        }
        cache_eligible = (
            not handoff
            and not telemetry["did_fallback"]
            and not telemetry["is_oos"]
            and not telemetry["is_ambiguous"]
            and category != "fraud"
        )
        if cache_eligible:
            telemetry["fallback_reason_code"] = telemetry.get("fallback_reason", "")
            telemetry_snapshot = {
                key: telemetry.get(key) for key in _CACHE_TELEMETRY_KEYS
            }
            decision_result = DecisionResult(
                response=response_payload,
                telemetry=telemetry_snapshot,
                decision_path=decision_path[:],
            )
            POSITIVE_CACHE.set(cache_key, decision_result.to_cache())
        return QueryResponse(
            **response_payload,
            debug={"decision_path": decision_path}
            if http_request.headers.get("X-Debug") == "1"
            else None,
        )
    except Exception as exc:
        error_message = str(exc)
        decision_path.append("fallback:internal_error")
        telemetry["did_fallback"] = True
        telemetry["fallback_reason"] = "internal_error"
        telemetry["fallback_reason_code"] = "internal_error"
        telemetry["citations_count"] = 0
        telemetry["confidence"] = 20
        telemetry["handoff"] = True
        telemetry["handoff_reason"] = "internal_error"
        inc_counter("query_fallback_total", {"fallback_reason_code": "internal_error"})
        inc_counter("query_handoff_total", {"handoff_reason_code": "internal_error"})
        telemetry_logger.exception("query_failed", exc_info=exc)
        timings["fallback"] = _ms_nonzero(1)
        observe_ms(
            "query_stage_ms",
            timings["fallback"],
            {"channel": request.channel, "stage": "fallback"},
        )
        tokens_out_est = estimate_tokens("حدث خطأ داخلي. حاول مرة أخرى.")
        telemetry["tokens_out_est"] = tokens_out_est
        telemetry["cost_usd_est"] = estimate_cost_usd(tokens_in_est, tokens_out_est)
        inc_counter("query_tokens_out_total", value=tokens_out_est)
        return QueryResponse(
            answer="حدث خطأ داخلي. حاول مرة أخرى.",
            steps=[],
            citations=[],
            confidence=0.2,
            category="unknown",
            risk_level="low",
            handoff=True,
            handoff_reason=localize_reason("internal_error", "ar-SA"),
            handoff_payload=None,
            debug={"decision_path": decision_path}
            if http_request.headers.get("X-Debug") == "1"
            else None,
        )
    finally:
        if telemetry["latency_ms"] is None:
            telemetry["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
        timings["total"] = _ms_nonzero(telemetry["latency_ms"])
        observe_ms(
            "query_latency_ms",
            _ms_nonzero(telemetry["latency_ms"]),
            {"channel": request.channel},
        )
        if not telemetry.get("fallback_reason_code"):
            telemetry["fallback_reason_code"] = telemetry.get("fallback_reason", "")
        if error_message:
            telemetry["error"] = error_message
        telemetry_logger.info(json.dumps(telemetry, ensure_ascii=False))
