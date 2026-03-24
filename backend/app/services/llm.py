from __future__ import annotations

import json
import logging
import ssl
from typing import List, Tuple

import httpx
from app.config import settings
from app.services.facts import FactHit
from app.services.retrieval import ContextChunk

logger = logging.getLogger(__name__)

_PROVIDER_DEFAULTS = {
    "kimi": {
        "api_key": "kimi_api_key",
        "base_url": "https://api.moonshot.ai/v1",
        "model": "kimi-k2.5",
        "log_event": "kimi_request_failed",
        "label": "Kimi",
    },
    "gemini": {
        "api_key": "gemini_api_key",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3.1-flash-lite-preview",
        "log_event": "gemini_request_failed",
        "label": "Gemini",
    },
}


def _summarize_facts(facts: List[FactHit]) -> str:
    lines = []
    for fact in facts:
        source = f" [المصدر: {fact.source}]" if fact.source else ""
        if fact.values:
            lines.append(f"- {fact.statement} (القيم: {fact.values}){source}")
        else:
            lines.append(f"- {fact.statement}{source}")
    return "\n".join(lines)


def _summarize_contexts(contexts: List[ContextChunk]) -> str:
    lines = []
    for ctx in contexts[:3]:
        snippet = " ".join(ctx.text.split())
        if len(snippet) > 280:
            snippet = snippet[:277].rstrip() + "..."
        lines.append(
            f"- المصدر: {ctx.source} | المعرّف: {ctx.chunk_id} | الصلة: {ctx.score:.2f} | النص: {snippet}"
        )
    return "\n".join(lines)


def _default_steps(has_evidence: bool) -> List[str]:
    if has_evidence:
        return [
            "تحقق من مطابقة الاستفسار مع الحقائق المعروضة.",
            "قدّم الإجابة للعميل بصياغة واضحة ومباشرة.",
            "إذا احتاج العميل تفصيلاً إضافياً، ارجع للمستندات الداعمة.",
        ]
    return [
        "أبلغ العميل بعدم توفر أدلة كافية للرد.",
        "حوّل الحالة للقسم المختص مع ملخص مختصر.",
        "سجّل سبب التحويل ضمن الحوكمة.",
    ]


def _generate_local_answer(
    facts: List[FactHit], contexts: List[ContextChunk]
) -> Tuple[str, List[str]]:
    if facts:
        answer = "استناداً إلى الحقائق المتاحة:\n" + _summarize_facts(facts)
        return answer, _default_steps(True)

    if contexts:
        answer = "استناداً إلى المقاطع المرجعية المتاحة:\n" + _summarize_contexts(contexts)
        return answer, _default_steps(True)

    answer = "لا تتوفر أدلة كافية للإجابة حالياً. يُرجى تحويل الطلب للجهة المختصة."
    return answer, _default_steps(False)


def _system_prompt(locale: str) -> str:
    if locale == "en-US":
        return (
            "You are a telecom CSR decision support assistant. "
            "Answer only from the provided evidence, stay concise, and do not invent facts. "
            "If the evidence is insufficient, say so clearly."
        )
    return (
        "أنت مساعد دعم قرار لموظف خدمة عملاء اتصالات. "
        "أجب فقط بالاعتماد على الأدلة المقدمة، وكن موجزاً، ولا تختلق حقائق. "
        "إذا كانت الأدلة غير كافية فاذكر ذلك بوضوح."
    )


def _build_messages(
    question: str, facts: List[FactHit], contexts: List[ContextChunk], locale: str
) -> list[dict[str, str]]:
    facts_block = _summarize_facts(facts) if facts else "- لا توجد حقائق مطابقة."
    contexts_block = _summarize_contexts(contexts) if contexts else "- لا توجد مقاطع داعمة."
    if locale == "en-US":
        user_prompt = (
            f"Question:\n{question}\n\n"
            f"Facts:\n{facts_block}\n\n"
            f"Context:\n{contexts_block}\n\n"
            "Write a short answer for the CSR in English."
        )
    else:
        user_prompt = (
            f"السؤال:\n{question}\n\n"
            f"الحقائق:\n{facts_block}\n\n"
            f"السياق:\n{contexts_block}\n\n"
            "اكتب إجابة عربية قصيرة وواضحة للموظف."
        )
    return [
        {"role": "system", "content": _system_prompt(locale)},
        {"role": "user", "content": user_prompt},
    ]


def _provider_config(provider: str) -> dict[str, str]:
    if provider not in _PROVIDER_DEFAULTS:
        raise RuntimeError(f"Unsupported LLM_PROVIDER={provider}")
    defaults = _PROVIDER_DEFAULTS[provider]
    api_key = getattr(settings, defaults["api_key"])
    if not api_key:
        env_name = defaults["api_key"].upper()
        raise RuntimeError(f"{env_name} is required when LLM_PROVIDER={provider}")
    return {
        "api_key": api_key,
        "base_url": settings.llm_base_url or defaults["base_url"],
        "model": settings.llm_model or defaults["model"],
        "log_event": defaults["log_event"],
        "label": defaults["label"],
    }


def _openai_compatible_chat_completion(
    provider: str, messages: list[dict[str, str]]
) -> str:
    provider_cfg = _provider_config(provider)
    endpoint = provider_cfg["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": provider_cfg["model"],
        "messages": messages,
        "temperature": 0.2,
    }
    verify: str | bool = settings.ssl_cert_file or True

    try:
        with httpx.Client(
            timeout=settings.llm_timeout_seconds,
            verify=verify,
            trust_env=True,
        ) as client:
            response = client.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {provider_cfg['api_key']}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:500]
        logger.warning(
            provider_cfg["log_event"],
            extra={
                "provider": provider,
                "status_code": exc.response.status_code,
                "body_preview": body,
            },
        )
        raise RuntimeError(
            f"{provider_cfg['label']} HTTP {exc.response.status_code}: {body}"
        ) from exc
    except httpx.ConnectError as exc:
        error_text = str(exc)[:200]
        if isinstance(exc.__cause__, ssl.SSLError) or "CERTIFICATE_VERIFY_FAILED" in error_text:
            raise RuntimeError(
                f"{provider_cfg['label']} SSL error: {error_text}"
            ) from exc
        raise RuntimeError(
            f"{provider_cfg['label']} network error: {error_text}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            f"{provider_cfg['label']} timeout after {settings.llm_timeout_seconds}s"
        ) from exc
    except httpx.TransportError as exc:
        raise RuntimeError(
            f"{provider_cfg['label']} transport error: {str(exc)[:200]}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"{provider_cfg['label']} returned non-JSON response"
        ) from exc

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"{provider_cfg['label']} response missing choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            f"{provider_cfg['label']} response missing message content"
        )
    return content.strip()


def generate_answer(
    question: str, facts: List[FactHit], contexts: List[ContextChunk], locale: str
) -> Tuple[str, List[str]]:
    provider = settings.llm_provider.lower().strip()
    if provider == "local":
        return _generate_local_answer(facts, contexts)

    if provider not in _PROVIDER_DEFAULTS:
        raise RuntimeError(f"Unsupported LLM_PROVIDER={provider}")

    answer = _openai_compatible_chat_completion(
        provider, _build_messages(question, facts, contexts, locale)
    )
    return answer, _default_steps(bool(facts or contexts))
