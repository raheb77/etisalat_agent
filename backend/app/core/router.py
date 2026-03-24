from typing import Optional, Tuple

CATEGORIES = {
    "billing",
    "network",
    "plans",
    "roaming",
    "porting",
    "ownership",
    "complaints",
    "app_login",
    "unknown",
}

AUTO_ESCALATE = {"legal", "fraud", "security"}

KEYWORDS = {
    "billing": ["فاتورة", "فواتير", "رسوم", "billing", "invoice", "مبلغ", "خصم"],
    "network": ["شبكة", "تغطية", "إشارة", "انترنت", "إنترنت", "سرعة", "network", "coverage"],
    "plans": ["باقة", "باقات", "ترقية", "تخفيض", "plan", "upgrade", "downgrade"],
    "roaming": ["تجوال", "روامينغ", "roaming", "international"],
    "porting": ["نقل الرقم", "نقل رقم", "تحويل الرقم", "porting", "mnp"],
    "ownership": ["نقل ملكية", "ملكية", "ownership", "transfer ownership"],
    "complaints": [
        "شكوى",
        "شكاوى",
        "اعتراض",
        "complaint",
        "dispute",
        "اشتكي",
        "أشتكي",
        "تصعيد",
        "escalate",
        "escalation",
    ],
    "app_login": ["تسجيل الدخول", "رمز", "OTP", "mystc", "login", "password"],
}

AUTO_ESCALATE_KEYWORDS = {
    "legal": [
        "استشارة قانونية",
        "تفسير قانوني",
        "راي قانوني",
        "رأي قانوني",
        "legal advice",
        "legal interpretation",
        "محامي",
        "هل يحق",
    ],
    "fraud": ["احتيال", "fraud", "سرقة"],
    "security": ["اختراق", "أمني", "security", "breach", "compromise", "إجراء عاجل"],
}


def _keyword_match(question: str, keywords: list[str]) -> bool:
    q = question.lower()
    return any(k.lower() in q for k in keywords)


def route(question: str, category_hint: Optional[str]) -> Tuple[str, str]:
    if category_hint in AUTO_ESCALATE or category_hint in CATEGORIES:
        category = category_hint
    else:
        category = None

    if category is None:
        # Treat legal interpretation/advice as sensitive, but let direct factual
        # telecom-policy lookups fall through to their factual category when possible.
        for auto_cat, keys in AUTO_ESCALATE_KEYWORDS.items():
            if _keyword_match(question, keys):
                return auto_cat, "high"

        for cat, keys in KEYWORDS.items():
            if _keyword_match(question, keys):
                category = cat
                break

    if category is None:
        category = "unknown"

    if category in AUTO_ESCALATE:
        return category, "high"
    if category in {"complaints", "billing"}:
        return category, "medium"
    return category, "low"


def classify(category_hint: Optional[str]) -> str:
    if category_hint and (category_hint in CATEGORIES or category_hint in AUTO_ESCALATE):
        return category_hint
    return "unknown"
