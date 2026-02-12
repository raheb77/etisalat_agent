from app.core.confidence import compute_confidence


def test_confidence_clamps_low():
    assert compute_confidence(0, 0.0, conflict_detected=True, risk_level="high") == 0.0


def test_confidence_clamps_high():
    assert compute_confidence(10, 1.0, conflict_detected=False, risk_level="low") == 1.0


def test_confidence_adds_fact_bonus():
    assert compute_confidence(1, 0.0, conflict_detected=False, risk_level="low") == 0.35
