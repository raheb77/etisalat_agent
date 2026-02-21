from __future__ import annotations

import os

from app.services.cache import TTLCache


def _clamp_ttl(value: int, low: int = 30, high: int = 120) -> int:
    return max(low, min(high, value))


POSITIVE_CACHE = TTLCache(max_items=256, ttl_seconds=60)
NEGATIVE_CACHE_TTL = _clamp_ttl(int(os.getenv("NEGATIVE_CACHE_TTL_SECONDS", "60")))
NEGATIVE_CACHE = TTLCache(max_items=256, ttl_seconds=NEGATIVE_CACHE_TTL)


def build_cache_key(question: str, locale: str, channel: str) -> str:
    normalized = " ".join(question.split()).lower()
    return f"{normalized}|{locale}|{channel}"
