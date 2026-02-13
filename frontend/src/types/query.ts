export type Citation = {
  source: string;
  chunk_id: string;
  score: number;
};

export type HandoffPayload = {
  team: string;
  summary: string;
  evidence: string[];
};

export type QueryResponse = {
  answer: string;
  steps?: string[];
  citations: Citation[];
  confidence: number;
  category: string;
  risk_level: string;
  handoff: boolean;
  handoff_reason: string;
  handoff_payload?: HandoffPayload | null;
};

export type QueryRequest = {
  question: string;
  category_hint?: string;
  locale: string;
  channel: string;
};
