import { localizeReason } from "../config/reasonI18n";
import {
  getConfidenceBand,
  getConfidenceLabel,
  type ConfidenceBand,
} from "./confidence";
import { computeHandoffMode, type HandoffMode } from "./handoff";

type UiLocale = "ar-SA" | "en-US";

type HandoffUiParams = {
  confidence: number;
  backendReason?: string;
  category?: string;
  locale: UiLocale;
  handoff?: boolean;
  citationsCount?: number;
};

type HandoffUiState = {
  confidenceBand: ConfidenceBand;
  confidenceLabel: string;
  shouldHandoff: boolean;
  bannerText: string;
  reasonText?: string;
  reasonVisibility: "hidden" | "shown";
  handoffMode: HandoffMode;
};

function handoffTitle(locale: UiLocale): string {
  return locale === "ar-SA" ? "يتطلب تحويل للموظف" : "Handoff required";
}

export function getHandoffUiState(params: HandoffUiParams): HandoffUiState {
  const confidenceBand = getConfidenceBand(params.confidence);
  const confidenceLabel = getConfidenceLabel(confidenceBand, params.locale);
  const specificReason = localizeReason(params.backendReason, params.locale);
  const reasonText = specificReason ?? undefined;
  const reasonVisibility: "hidden" | "shown" = "shown";
  const subtitle = reasonText ?? confidenceLabel;
  const bannerText = `${handoffTitle(params.locale)}. ${subtitle}`;
  const handoffMode = computeHandoffMode({
    handoff: params.handoff,
    category: params.category,
    confidence: params.confidence,
    citationsCount: params.citationsCount,
    handoffReason: params.backendReason ?? null,
  });

  return {
    confidenceBand,
    confidenceLabel,
    shouldHandoff: handoffMode !== "none",
    bannerText,
    reasonText,
    reasonVisibility,
    handoffMode,
  };
}

export function __devHandoffUiExamples() {
  return [
    getHandoffUiState({
      confidence: 65,
      backendReason: "Low confidence",
      locale: "en-US",
      handoff: true,
      citationsCount: 2,
    }),
    getHandoffUiState({
      confidence: 20,
      backendReason: "High risk category",
      locale: "ar-SA",
      category: "fraud",
      handoff: false,
      citationsCount: 0,
    }),
  ];
}
// console.log(__devHandoffUiExamples());
