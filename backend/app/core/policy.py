from typing import Dict

AUTO_ESCALATE = {"legal", "fraud", "security"}

TEAM_MAP = {
    "billing": "Billing L2",
    "network": "Network Ops L2",
    "porting": "Porting Desk",
    "complaints": "Complaints/CST Desk",
    "plans": "CSR Supervisor",
    "roaming": "CSR Supervisor",
    "ownership": "CSR Supervisor",
    "app_login": "CSR Supervisor",
}


def policy_decision(
    category: str, risk_level: str, confidence: float, has_fact_hits: bool
) -> Dict[str, object]:
    if risk_level == "high":
        return {
            "allow_answer": False,
            "handoff": True,
            "handoff_reason": "High risk category",
            "team": "Compliance/Security",
        }

    if category in AUTO_ESCALATE:
        return {
            "allow_answer": False,
            "handoff": True,
            "handoff_reason": "High risk category",
            "team": "Compliance/Security",
        }

    # Complaint/escalation requests should consistently go to the escalation path
    # even when confidence is high, because the user is asking for a formal complaint flow.
    if category == "complaints":
        return {
            "allow_answer": False,
            "handoff": True,
            "handoff_reason": "Policy restriction",
            "team": TEAM_MAP.get(category, "Complaints/CST Desk"),
        }

    if confidence < 0.85:
        return {
            "allow_answer": False,
            "handoff": True,
            "handoff_reason": "Low confidence",
            "team": TEAM_MAP.get(category, "CSR Supervisor"),
        }

    if category == "unknown":
        return {
            "allow_answer": False,
            "handoff": True,
            "handoff_reason": "Out of scope",
            "team": TEAM_MAP.get(category, "CSR Supervisor"),
        }

    return {
        "allow_answer": True,
        "handoff": False,
        "handoff_reason": "",
        "team": TEAM_MAP.get(category, "CSR Supervisor"),
    }


def risk_level(category: str) -> str:
    if category in AUTO_ESCALATE:
        return "high"
    if category == "unknown":
        return "medium"
    return "low"


def should_escalate(category: str, confidence: float, threshold: float = 0.85) -> tuple[bool, str]:
    if category in AUTO_ESCALATE:
        return True, "Policy restriction"
    if category == "complaints":
        return True, "Policy restriction"
    if confidence < threshold:
        return True, "Low confidence"
    if category == "unknown":
        return True, "Insufficient knowledge evidence"
    return False, ""
