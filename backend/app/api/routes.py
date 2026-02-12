import time

from fastapi import APIRouter, HTTPException, Request

from app.core import citations, confidence, policy, router, sanitizer
from app.schemas.query import QueryRequest, QueryResponse
from app.services import audit, facts, llm, retrieval

router_api = APIRouter()


@router_api.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router_api.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, http_request: Request) -> QueryResponse:
    start_time = time.monotonic()
    masked_question, has_pii, pii_types = sanitizer.sanitize_question(request.question)

    user_id = http_request.headers.get("X-User-ID", "unknown")

    category, risk = router.route(masked_question, request.category_hint)

    fact_hits = facts.search_facts(masked_question, category)
    ctx = retrieval.retrieve_context(masked_question, category)
    cits = citations.build_citations(fact_hits, ctx)
    max_score = max([c.score for c in ctx], default=0.0)
    conf = confidence.compute_confidence(
        fact_hits_count=len(fact_hits),
        retrieval_score=max_score,
        conflict_detected=False,
        risk_level=risk,
    )

    decision = policy.policy_decision(category, risk, conf, bool(fact_hits) or bool(ctx))

    answer, steps = llm.generate_answer(masked_question, fact_hits, ctx, request.locale)
    if decision["handoff"] and category in {"legal", "fraud", "security"}:
        answer = "لا يمكن معالجة هذا الطلب هنا. سيتم تحويله إلى الجهة المختصة."

    latency_ms = int((time.monotonic() - start_time) * 1000)
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

    return QueryResponse(
        answer=answer,
        steps=steps,
        citations=cits,
        confidence=conf,
        category=category,
        risk_level=risk,
        handoff=decision["handoff"],
        handoff_reason=decision["handoff_reason"] if decision["handoff"] else None,
        handoff_payload={
            "team": decision["team"],
            "summary": f"ملخص السؤال: {masked_question}",
            "evidence": evidence_items if evidence_items else [f"{category}#no_evidence"],
        } if decision["handoff"] else None,
    )
