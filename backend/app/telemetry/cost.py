from __future__ import annotations

import os


def estimate_tokens(text: str) -> int:
    if not text:
        return 1
    return max(1, len(text) // 4)


def _env_float(name: str, default: float = 0.0) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def estimate_cost_usd(
    tokens_in: int,
    tokens_out: int,
    price_per_1k_in: float | None = None,
    price_per_1k_out: float | None = None,
) -> float:
    price_in = (
        _env_float("LLM_PRICE_PER_1K_IN", 0.0)
        if price_per_1k_in is None
        else price_per_1k_in
    )
    price_out = (
        _env_float("LLM_PRICE_PER_1K_OUT", 0.0)
        if price_per_1k_out is None
        else price_per_1k_out
    )
    cost = (tokens_in / 1000.0) * price_in + (tokens_out / 1000.0) * price_out
    return float(round(cost, 6))
