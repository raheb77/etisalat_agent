export type ConfidenceBand = "high" | "moderate" | "low";

function normalizeConfidence(confidence?: number): number {
  if (confidence === null || confidence === undefined) {
    return 0;
  }
  if (Number.isNaN(confidence)) {
    return 0;
  }
  return confidence;
}

export function getConfidenceBand(confidence?: number): ConfidenceBand {
  const value = normalizeConfidence(confidence);
  if (value >= 80) return "high";
  if (value >= 50) return "moderate";
  return "low";
}

export function getConfidenceLabel(
  band: ConfidenceBand,
  uiLocale: "ar-SA" | "en-US"
): string {
  const ar = uiLocale === "ar-SA";
  if (band === "high") return ar ? "ثقة عالية" : "High confidence";
  if (band === "moderate") return ar ? "ثقة متوسطة" : "Moderate confidence";
  return ar ? "ثقة منخفضة" : "Low confidence";
}

export function formatConfidencePct(confidence?: number): string {
  const value = normalizeConfidence(confidence);
  const rounded = Math.round(value);
  return `${rounded}%`;
}
