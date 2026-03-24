import { useEffect, useRef, useState } from "react";

import { ResponsePanel } from "./ResponsePanel";
import {
  formatConfidencePct,
} from "../utils/confidence";
import { getHandoffUiState } from "../utils/handoffUi";
import type { Message } from "../types/chat";
import type { QueryResponse } from "../types/query";

export type UiLocale = "ar-SA" | "en-US";

type ChatWindowProps = {
  messages: Message[];
  isLoading: boolean;
  onSend: (content: string) => void;
  locale: UiLocale;
  onLocaleChange: (value: UiLocale) => void;
  categoryHint: string;
  onCategoryHintChange: (value: string) => void;
};

const SCROLL_THRESHOLD = 48;
const EXAMPLE_QUESTIONS = [
  "ما مدة نقل الرقم؟",
  "كم سعر باقة 55 جيجا؟",
  "تعرضت لاحتيال وسحب رصيد",
] as const;

function extractTLDR(answer: string | undefined, uiLocale: UiLocale): string {
  const isArabicUi = uiLocale === "ar-SA";
  if (!answer || answer.trim() === "") {
    return isArabicUi ? "لا تتوفر إجابة." : "No answer available.";
  }

  const MAX_CHARS = 140;
  const sentenceEndPattern = isArabicUi ? /[.،؟!](\s|$)/ : /[.?!](\s|$)/;
  const match = answer.match(sentenceEndPattern);

  if (match?.index !== undefined && match.index + 1 <= MAX_CHARS) {
    return answer.slice(0, match.index + 1).trim();
  }

  if (answer.length <= MAX_CHARS) return answer.trim();

  const truncated = answer.slice(0, MAX_CHARS);
  const lastSpace = truncated.lastIndexOf(" ");
  if (lastSpace > Math.floor(MAX_CHARS * 0.6)) {
    return truncated.slice(0, lastSpace).trim() + "…";
  }
  return truncated.trim() + "…";
}

export function ChatWindow({
  messages,
  isLoading,
  onSend,
  locale,
  onLocaleChange,
  categoryHint,
  onCategoryHintChange,
}: ChatWindowProps) {
  const bubbleWidthClass =
    "w-full max-w-[90%] sm:max-w-[80%] lg:max-w-[70%]";
  const isArabicUi = locale === "ar-SA";
  const examplesLabel = isArabicUi ? "أسئلة مقترحة:" : "Example questions:";
  const [draft, setDraft] = useState("");
  const containerRef = useRef<HTMLDivElement | null>(null);
  const shouldAutoScrollRef = useRef(true);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !shouldAutoScrollRef.current) {
      return;
    }

    const scrollToBottom = () => {
      container.scrollTop = container.scrollHeight;
    };

    scrollToBottom();
  }, [messages]);

  const handleScroll = () => {
    const container = containerRef.current;
    if (!container) return;
    const distanceToBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;
    shouldAutoScrollRef.current = distanceToBottom <= SCROLL_THRESHOLD;
  };

  const handleSend = () => {
    const trimmed = draft.trim();
    if (!trimmed || isLoading) {
      return;
    }
    onSend(trimmed);
    setDraft("");
    shouldAutoScrollRef.current = true;
  };

  const normalizePayload = (payload: Message["payload"]): QueryResponse => {
    const raw = payload as unknown as {
      answer?: string;
      steps?: string[];
      citations?: Array<{
        source?: string;
        chunk?: string;
        chunk_id?: string;
        score?: number;
      }>;
      confidence?: number;
      category?: string;
      handoff?: boolean;
      handoff_reason?: string;
      risk_level?: string;
      handoff_payload?: QueryResponse["handoff_payload"];
    };

    const citations =
      raw.citations?.map((citation) => ({
        source: citation.source ?? "",
        chunk_id: citation.chunk_id ?? citation.chunk ?? "",
        score: typeof citation.score === "number" ? citation.score : 0,
      })) ?? [];

    return {
      answer: raw.answer ?? "",
      steps: raw.steps ?? [],
      citations,
      confidence: typeof raw.confidence === "number" ? raw.confidence : 0,
      category: raw.category ?? "Unknown",
      risk_level: raw.risk_level ?? "unknown",
      handoff: Boolean(raw.handoff),
      handoff_reason: raw.handoff_reason ?? "",
      handoff_payload: raw.handoff_payload ?? null,
    };
  };

  const getConfidenceBadgeClass = (confidence: number) => {
    if (confidence > 0.8) {
      return "border-emerald-200 bg-emerald-100 text-emerald-700";
    }
    if (confidence > 0.5) {
      return "border-amber-200 bg-amber-100 text-amber-700";
    }
    return "border-rose-200 bg-rose-100 text-rose-700";
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 space-y-3 overflow-y-auto rounded-2xl border border-slate-200 bg-white/80 p-4"
        data-testid="message-list"
      >
        {messages.length === 0 ? (
          <div className="text-sm text-slate-500">
            Ask a telecom CSR question to see grounded answers, confidence, and citations.
          </div>
        ) : (
          messages.map((message) => {
            const isUser = message.role === "user";
            const normalizedPayload = message.payload
              ? normalizePayload(message.payload)
              : null;
            const confidence = normalizedPayload?.confidence ?? 0;
            const confidencePercentValue = Math.round(confidence * 100);
            const confidencePercent = formatConfidencePct(confidencePercentValue);
            const assistantPreview = normalizedPayload
              ? extractTLDR(normalizedPayload.answer, locale)
              : null;
            const uiState = normalizedPayload
              ? getHandoffUiState({
                  confidence: confidencePercentValue,
                  backendReason: normalizedPayload.handoff_reason,
                  category: normalizedPayload.category,
                  locale,
                  handoff: normalizedPayload.handoff,
                  citationsCount: normalizedPayload.citations?.length,
                })
              : null;
            return (
              <div
                key={message.id}
                className={`flex flex-col gap-3 ${
                  isUser ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`${bubbleWidthClass} rounded-2xl px-4 py-2 text-sm shadow-soft ${
                    isUser
                      ? "bg-blue-600 text-white"
                      : "bg-zinc-800 text-zinc-100"
                  }`}
                  dir={isArabicUi ? "rtl" : "ltr"}
                  lang={isArabicUi ? "ar" : "en"}
                >
                  <span className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                    {isUser
                      ? message.content
                      : assistantPreview ??
                        (message.content ||
                          (message.status === "pending" ? "…" : ""))}
                  </span>
                </div>
                {!isUser && normalizedPayload && (
                  <div className="w-full max-w-3xl space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-semibold ${getConfidenceBadgeClass(
                          confidence
                        )}`}
                      >
                        {confidencePercent}
                      </span>
                      {uiState && (
                        <span className="text-xs font-semibold text-slate-500">
                          {uiState.confidenceLabel}
                        </span>
                      )}
                      {uiState?.shouldHandoff && (
                        <div
                          data-testid="handoff-banner"
                          className={`w-full rounded-2xl border px-4 py-3 text-sm shadow-sm ${
                            uiState.handoffMode === "forced"
                              ? "border-amber-400 bg-gradient-to-r from-amber-100 via-amber-50 to-orange-50 text-amber-950"
                              : "border-amber-300 bg-amber-50/90 text-amber-900"
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-current/15 bg-white/60 text-xs font-bold">
                              !
                            </span>
                            <div className="space-y-1">
                              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">
                                {locale === "ar-SA" ? "يتطلب مراجعة" : "Review required"}
                              </div>
                              <span className="font-semibold">{uiState.bannerText}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-soft">
                      <ResponsePanel data={normalizedPayload} uiLocale={locale} />
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-soft">
        <div className="flex flex-col gap-3">
          <textarea
            className="min-h-[96px] w-full resize-none rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-200"
            placeholder="Type your message..."
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleSend();
              }
            }}
            data-testid="question-input"
          />
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-slate-500">
              {examplesLabel}
            </span>
            {EXAMPLE_QUESTIONS.map((question) => (
              <button
                key={question}
                type="button"
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700"
                onClick={() => setDraft(question)}
              >
                {question}
              </button>
            ))}
          </div>
          <div className="grid gap-3 md:grid-cols-[160px_1fr]">
            <div className="space-y-2">
              <label
                className="text-xs font-semibold uppercase tracking-wide text-slate-500"
                htmlFor="chatLocale"
              >
                Locale
              </label>
              <select
                id="chatLocale"
                className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-200"
                value={locale}
                onChange={(event) =>
                  onLocaleChange(event.target.value as "ar-SA" | "en-US")
                }
                data-testid="locale-select"
              >
                <option value="ar-SA">ar-SA</option>
                <option value="en-US">en-US</option>
              </select>
            </div>
            <div className="space-y-2">
              <label
                className="text-xs font-semibold uppercase tracking-wide text-slate-500"
                htmlFor="categoryHint"
              >
                Category hint (optional)
              </label>
              <input
                id="categoryHint"
                type="text"
                className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-200"
                placeholder="billing, network, plans"
                value={categoryHint}
                onChange={(event) => onCategoryHintChange(event.target.value)}
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-xs text-slate-500">
              {isLoading ? "Loading response..." : "Enter to send · Shift+Enter for newline"}
            </div>
            <button
              type="button"
              className="rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-soft transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
              onClick={handleSend}
              disabled={isLoading}
              data-testid="send-button"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
