import { localizeReason } from "../config/reasonI18n";

export type ConfidenceBand = "low" | "medium" | "high";

type UiLocale = "ar-SA" | "en-US";

function normalizeConfidencePct(confidence?: number): number {
  if (confidence === null || confidence === undefined) {
    return 0;
  }
  if (Number.isNaN(confidence)) {
    return 0;
  }
  if (confidence >= 0 && confidence <= 1) {
    return confidence * 100;
  }
  return confidence;
}

export function getConfidenceBand(confidence?: number): ConfidenceBand {
  const value = normalizeConfidencePct(confidence);
  if (value >= 80) return "high";
  if (value >= 50) return "medium";
  return "low";
}

export function getConfidenceLabel(
  band: ConfidenceBand,
  uiLocale: UiLocale
): string {
  const ar = uiLocale === "ar-SA";
  if (band === "high") return ar ? "ثقة عالية" : "High confidence";
  if (band === "medium") return ar ? "ثقة متوسطة" : "Moderate confidence";
  return ar ? "ثقة منخفضة" : "Low confidence";
}

export function formatConfidencePct(confidence?: number): string {
  const value = normalizeConfidencePct(confidence);
  const rounded = Math.round(value);
  return `${rounded}%`;
}

export function resolveConfidenceReason(opts: {
  reason?: string | null;
  confidence?: number;
  uiLocale: UiLocale;
}): string {
  const band = getConfidenceBand(opts.confidence);
  const fallback = getConfidenceLabel(band, opts.uiLocale);
  const rawReason = opts.reason?.trim();
  if (!rawReason) return fallback;
  const localized = localizeReason(rawReason, opts.uiLocale);
  return localized ?? fallback;
}

export function __devConfidenceExamples() {
  return [
    {
      confidence: 65,
      band: getConfidenceBand(65),
      labelEn: getConfidenceLabel(getConfidenceBand(65), "en-US"),
      labelAr: getConfidenceLabel(getConfidenceBand(65), "ar-SA"),
    },
    {
      confidence: 20,
      band: getConfidenceBand(20),
      labelEn: getConfidenceLabel(getConfidenceBand(20), "en-US"),
      labelAr: getConfidenceLabel(getConfidenceBand(20), "ar-SA"),
    },
  ];
}
// console.log(__devConfidenceExamples());
