from app.core.policy import policy_decision


def test_policy_high_risk_handoff():
    decision = policy_decision("billing", "high", 0.9, True)
    assert decision["handoff"] is True
    assert decision["handoff_reason"] == "High risk category"


def test_policy_auto_escalate_team():
    decision = policy_decision("legal", "high", 0.9, True)
    assert decision["handoff"] is True
    assert decision["team"] == "Compliance/Security"


def test_policy_low_confidence():
    decision = policy_decision("network", "low", 0.5, True)
    assert decision["handoff"] is True
    assert decision["handoff_reason"] == "Low confidence"


def test_policy_unknown_out_of_scope():
    decision = policy_decision("unknown", "medium", 0.9, False)
    assert decision["handoff"] is True
    assert decision["handoff_reason"] == "Out of scope"


def test_policy_allow_answer():
    decision = policy_decision("billing", "medium", 0.9, True)
    assert decision["allow_answer"] is True
    assert decision["handoff"] is False


def test_policy_complaints_always_escalate():
    decision = policy_decision("complaints", "medium", 0.95, True)
    assert decision["handoff"] is True
    assert decision["handoff_reason"] == "Policy restriction"
