def clamp(value: float, low: float, high: float) -> float:
    if value < low:
        return low
    if value > high:
        return high
    return value


def compute_confidence(
    fact_hits_count: int,
    retrieval_score: float,
    conflict_detected: bool,
    risk_level: str,
) -> float:
    facts_score = min(0.6, 0.15 * fact_hits_count)
    penalty = 0.0
    if conflict_detected:
        penalty += 0.25
    if risk_level == "high":
        penalty += 0.15

    confidence = 0.2 + facts_score + 0.8 * retrieval_score - penalty
    return float(clamp(confidence, 0.0, 1.0))
