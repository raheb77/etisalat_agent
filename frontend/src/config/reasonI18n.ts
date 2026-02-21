type ReasonLocale = "ar-SA" | "en-US";

type ReasonMap = Record<string, Record<ReasonLocale, string>>;

export const reasonI18n: ReasonMap = {
  "high risk category": {
    "ar-SA": "تصنيف عالي الخطورة",
    "en-US": "High risk category",
  },
  "no citations returned": {
    "ar-SA": "لا توجد اقتباسات",
    "en-US": "No citations returned",
  },
  "low confidence": {
    "ar-SA": "ثقة منخفضة",
    "en-US": "Low confidence",
  },
  "moderate confidence": {
    "ar-SA": "ثقة متوسطة",
    "en-US": "Moderate confidence",
  },
  "medium confidence": {
    "ar-SA": "ثقة متوسطة",
    "en-US": "Moderate confidence",
  },
  "high confidence": {
    "ar-SA": "ثقة عالية",
    "en-US": "High confidence",
  },
};

const GENERIC_CONFIDENCE_KEYS = new Set([
  "low confidence",
  "moderate confidence",
  "medium confidence",
  "high confidence",
]);

function normalizeReason(reason: string): string {
  return reason.trim().toLowerCase();
}

export function localizeReason(
  reason: string | undefined,
  locale: ReasonLocale
): string | undefined {
  const raw = reason?.trim();
  if (!raw) return undefined;
  const key = normalizeReason(raw);
  if (GENERIC_CONFIDENCE_KEYS.has(key)) return undefined;
  const entry = reasonI18n[key];
  if (entry) return entry[locale];
  return locale === "en-US" ? raw : undefined;
}

// __dev examples:
// localizeReason("High risk category", "ar-SA") => "تصنيف عالي الخطورة"
// localizeReason("Moderate confidence", "en-US") => undefined
