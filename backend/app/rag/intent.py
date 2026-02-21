from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass
class IntentResult:
    primary: str
    secondary: List[str]
    score: float


_INTENT_ORDER: List[str] = [
    "fraud",
    "billing",
    "porting",
    "plans",
    "network",
    "general",
]

_KEYWORDS: Dict[str, Iterable[str]] = {
    "fraud": [
        "احتيال",
        "سحب رصيد",
        "رسائل مشبوهة",
        "phishing",
        "fraud",
        "scam",
    ],
    "billing": [
        "فاتورة",
        "فوتر",
        "رسوم",
        "اعتراض",
        "شكوى",
        "billing",
        "invoice",
        "fee",
        "complaint",
    ],
    "porting": [
        "نقل رقم",
        "تحويل رقم",
        "mnp",
        "porting",
        "transfer number",
    ],
    "plans": [
        "باقة",
        "جيجا",
        "سوا",
        "مفوتر",
        "باقات",
        "plan",
        "bundle",
        "gb",
    ],
    "network": [
        "تغطية",
        "شبكة",
        "سرعة",
        "5g",
        "network",
        "coverage",
        "speed",
    ],
}


def _count_matches(query: str, keywords: Iterable[str]) -> int:
    return sum(1 for keyword in keywords if keyword in query)


def detect_intent(query: str) -> IntentResult:
    normalized = query.strip().lower()
    if not normalized:
        return IntentResult(primary="general", secondary=[], score=0.0)

    matches: List[Tuple[str, int]] = []
    for intent, keywords in _KEYWORDS.items():
        count = _count_matches(normalized, keywords)
        if count > 0:
            matches.append((intent, count))

    if not matches:
        return IntentResult(primary="general", secondary=[], score=0.0)

    total_matches = sum(count for _, count in matches)
    score = min(1.0, total_matches / 3)

    intents = {intent for intent, _ in matches}
    primary = next((intent for intent in _INTENT_ORDER if intent in intents), "general")
    secondary = [intent for intent in _INTENT_ORDER if intent in intents and intent != primary]

    return IntentResult(primary=primary, secondary=secondary, score=score)
