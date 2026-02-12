import re
from typing import List, Tuple

PII_PATTERNS = {
    "phone": re.compile(r"(\+9665\d{8}\b|05\d{8}\b)"),
    "iban": re.compile(r"\bSA\d{2}[A-Z0-9]{18}\b"),
    "card": re.compile(r"\b\d{13,19}\b"),
    "national_id": re.compile(r"\b\d{10}\b"),
}


def sanitize_question(text: str) -> Tuple[str, bool, List[str]]:
    """
    Sanitize potential PII using simple rule-based patterns.

    Limitations:
    - Regex-based detection can yield false positives/negatives.
    - Numeric sequences may match non-PII values.
    - This does not validate ownership or check against authoritative sources.
    """
    sanitized = text
    pii_types: List[str] = []

    for pii_type, pattern in PII_PATTERNS.items():
        if pattern.search(sanitized):
            pii_types.append(pii_type)
            sanitized = pattern.sub("***", sanitized)

    pii_detected = len(pii_types) > 0
    return sanitized, pii_detected, pii_types


def detect_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern in PII_PATTERNS.values())


def mask_pii(text: str) -> Tuple[str, bool]:
    masked, pii_detected, _ = sanitize_question(text)
    return masked, pii_detected
