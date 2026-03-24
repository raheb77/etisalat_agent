from __future__ import annotations

from typing import Tuple

from app.rag.normalize import normalize_text

_RAW_VAGUE_PHRASES = [
    "عندي مشكلة",
    "عندي مشكله",
    "مشكلة",
    "مشكلتي",
    "ساعدني",
    "ابي اسال",
    "أبي أسأل",
    "ممكن",
    "ابغى مساعدة",
    "ابغى مساعده",
    "احتاج مساعدة",
]

_RAW_DOMAIN_ANCHORS = [
    "فاتورة",
    "فواتير",
    "باقة",
    "باقات",
    "جيجا",
    "شريحة",
    "سوا",
    "مفوتر",
    "نقل",
    "تغطية",
    "شبكة",
    "5g",
    "سرعة",
    "رسوم",
    "سعر",
    "سداد",
    "شكاوى",
    "شكوى",
    "اعتراض",
    "انترنت",
    "رصيد",
    "احتيال",
    "سحب",
    "stc",
]

def normalize_arabic(text: str) -> str:
    return normalize_text(text)


_VAGUE_PHRASES = [normalize_arabic(p).lower() for p in _RAW_VAGUE_PHRASES]
_DOMAIN_ANCHORS = [normalize_arabic(a).lower() for a in _RAW_DOMAIN_ANCHORS]


def detect_ambiguity(query: str) -> Tuple[bool, float, str]:
    normalized = normalize_arabic(query).lower()
    if not normalized:
        return False, 0.0, ""

    words = [w for w in normalized.split() if w]
    if len(words) > 4:
        return False, 0.0, ""

    if not any(phrase in normalized for phrase in _VAGUE_PHRASES):
        return False, 0.0, ""

    if any(anchor in normalized for anchor in _DOMAIN_ANCHORS):
        return False, 0.0, ""

    return True, 0.9, "vague_short_query"


if __name__ == "__main__":
    print(detect_ambiguity("عندي مشكلة"))
    print(detect_ambiguity("عندي مشكلة في الفاتورة"))
