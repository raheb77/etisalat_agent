export type EvidenceLevel = "strong" | "moderate" | "limited" | "none";

function clampScore(value: number): number {
  if (Number.isNaN(value)) return 0;
  return Math.min(1, Math.max(0, value));
}

export function computeEvidenceLevel(
  citations?: Array<{ score?: number }>
): EvidenceLevel {
  if (!citations || citations.length === 0) {
    return "none";
  }

  const topScore = citations.reduce((maxScore, citation) => {
    const score = clampScore(citation.score ?? 0);
    return Math.max(maxScore, score);
  }, 0);

  if (topScore >= 0.8) {
    return "strong";
  }

  if (topScore >= 0.5) {
    return "moderate";
  }

  return "limited";
}

export function getEvidenceLabel(
  level: EvidenceLevel,
  uiLocale: "ar-SA" | "en-US"
): string {
  const ar = uiLocale === "ar-SA";
  if (level === "strong") return ar ? "أدلة قوية" : "Strong evidence";
  if (level === "moderate") return ar ? "أدلة متوسطة" : "Moderate evidence";
  if (level === "limited") return ar ? "أدلة محدودة" : "Limited evidence";
  return ar ? "لا توجد أدلة داعمة" : "No supporting evidence";
}
