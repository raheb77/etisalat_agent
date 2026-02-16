export type HandoffMode = "none" | "suggested" | "forced";

type HandoffInput = {
  handoff?: boolean;
  category?: string;
  confidence?: number;
  citationsCount?: number;
  handoffReason?: string | null;
};

function normalizeConfidence(value?: number): number | null {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return null;
  }
  if (value >= 0 && value <= 1) {
    return value * 100;
  }
  return value;
}

export function computeHandoffMode(input: HandoffInput): HandoffMode {
  const category = input.category?.trim().toLowerCase() ?? "";
  const confidence = normalizeConfidence(input.confidence);
  const citationsCount = input.citationsCount;

  if (["fraud", "legal", "security"].includes(category)) {
    return "forced";
  }

  if (confidence !== null && confidence < 35) {
    return "forced";
  }

  if (citationsCount === 0 && input.handoff === true) {
    return "forced";
  }

  if (input.handoff === true) {
    return "suggested";
  }

  return "none";
}
