from __future__ import annotations

import re

_ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670]")
_PUNCTUATION_NOISE = re.compile(r"[^\w\s\u0600-\u06FF]+")
_ARABIC_PUNCTUATION = re.compile(r"[؟،؛]")
_DIGIT_LATIN_BOUNDARY = re.compile(r"(?<=\d)(?=[A-Za-z])|(?<=[A-Za-z])(?=\d)")
_WHITESPACE = re.compile(r"\s+")
_TATWEEL = "\u0640"
_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)


def normalize_text(text: str) -> str:
    normalized = text.translate(_DIGIT_TRANSLATION)
    normalized = _ARABIC_DIACRITICS.sub("", normalized)
    normalized = normalized.replace(_TATWEEL, "")
    normalized = normalized.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    normalized = normalized.replace("ى", "ي")
    normalized = _DIGIT_LATIN_BOUNDARY.sub(" ", normalized)
    normalized = normalized.lower()
    normalized = _ARABIC_PUNCTUATION.sub(" ", normalized)
    normalized = _PUNCTUATION_NOISE.sub(" ", normalized)
    normalized = _WHITESPACE.sub(" ", normalized)
    return normalized.strip()


_ALIAS_SEED_RULES = [
    ("مده", "مدة"),
    ("duration", "مدة"),
    ("تحويل الرقم", "نقل الرقم"),
    ("porting", "نقل الرقم"),
    ("كم يستغرق", "ما مدة"),
    ("كم ساعة يحتاج نقل الرقم كحد اقصى", "ما مدة نقل الرقم"),
    ("عرض 55 جيجا", "باقة 55 جيجا"),
]
_ALIAS_RULES = [
    (normalize_text(source), normalize_text(target))
    for source, target in _ALIAS_SEED_RULES
]


def expand_telecom_aliases(text: str) -> str:
    expanded = text
    for source, target in _ALIAS_RULES:
        expanded = re.sub(rf"(?<!\S){re.escape(source)}(?!\S)", target, expanded)
    return _WHITESPACE.sub(" ", expanded).strip()


def normalize_query(text: str) -> str:
    return expand_telecom_aliases(normalize_text(text))
