export type EvidenceLevel = "strong" | "limited" | "none";

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

  const total = citations.reduce((sum, citation) => {
    const score = citation.score ?? 0;
    return sum + clampScore(score);
  }, 0);
  const avg = total / citations.length;

  if (citations.length >= 3 && avg >= 0.75) {
    return "strong";
  }

  return "limited";
}

export function getEvidenceLabel(
  level: EvidenceLevel,
  uiLocale: "ar-SA" | "en-US"
): string {
  const ar = uiLocale === "ar-SA";
  if (level === "strong") return ar ? "أدلة قوية" : "Strong evidence";
  if (level === "limited") return ar ? "أدلة محدودة" : "Limited evidence";
  return ar ? "لا توجد أدلة داعمة" : "No supporting evidence";
}
