import type { QueryResponse } from "../types/query";

export const responseWithCitations: QueryResponse = {
  answer: "باقة 55 جيجا سعرها 120 ريال شهرياً.",
  steps: ["تحقق من الباقة عبر التطبيق.", "أكد تفاصيل التسعير قبل الاشتراك."],
  citations: [
    {
      source: "docs/plans/55gb.md",
      chunk_id: "plan-55gb-price",
      score: 0.92,
    },
  ],
  confidence: 0.82,
  category: "plans",
  risk_level: "low",
  handoff: false,
  handoff_reason: "",
  handoff_payload: null,
};

export const responseNoCitations: QueryResponse = {
  answer: "لا تتوفر معلومات مباشرة عن هذه الباقة حالياً.",
  steps: [],
  citations: [],
  confidence: 0.4,
  category: "plans",
  risk_level: "low",
  handoff: false,
  handoff_reason: "",
  handoff_payload: null,
};

export const responseWithHandoff: QueryResponse = {
  answer: "هذا الطلب يحتاج مراجعة.",
  steps: [],
  citations: [],
  confidence: 0.35,
  category: "fraud",
  risk_level: "high",
  handoff: true,
  handoff_reason: "High risk category",
  handoff_payload: null,
};
