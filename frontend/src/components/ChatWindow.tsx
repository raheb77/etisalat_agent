import { useEffect, useRef, useState } from "react";

import { ResponsePanel } from "./ResponsePanel";
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

function confidenceBand(pct: number): "high" | "moderate" | "low" {
  if (pct >= 80) return "high";
  if (pct >= 50) return "moderate";
  return "low";
}

function confidenceLabel(
  band: "high" | "moderate" | "low",
  uiLocale: UiLocale
): string {
  const ar = uiLocale === "ar-SA";
  if (band === "high") return ar ? "ثقة عالية" : "High confidence";
  if (band === "moderate") return ar ? "ثقة متوسطة" : "Moderate confidence";
  return ar ? "ثقة منخفضة" : "Low confidence";
}

function handoffTitle(uiLocale: UiLocale): string {
  return uiLocale === "ar-SA" ? "يتطلب تحويل للموظف" : "Handoff required";
}

function handoffSubtitle(opts: {
  handoffReason?: string;
  confidence?: number;
  uiLocale: UiLocale;
}): string {
  const reason = opts.handoffReason?.trim();
  if (reason) return reason;
  const pct = Math.max(0, Math.min(100, opts.confidence ?? 0));
  return confidenceLabel(confidenceBand(pct), opts.uiLocale);
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
      >
        {messages.length === 0 ? (
          <div className="text-sm text-slate-500">
            Start the conversation by asking a question.
          </div>
        ) : (
          messages.map((message) => {
            const isUser = message.role === "user";
            const normalizedPayload = message.payload
              ? normalizePayload(message.payload)
              : null;
            const confidence = normalizedPayload?.confidence ?? 0;
            const confidencePercent = `${Math.round(confidence * 100)}%`;
            const assistantPreview = normalizedPayload
              ? extractTLDR(normalizedPayload.answer, locale)
              : null;
            const band = confidenceBand(Math.round(confidence * 100));
            const bandLabel = confidenceLabel(band, locale);
            return (
              <div
                key={message.id}
                className={`flex flex-col gap-3 ${
                  isUser ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`rounded-2xl px-4 py-2 text-sm shadow-soft ${
                    isUser
                      ? "max-w-[75%] bg-blue-600 text-white"
                      : "max-w-[85%] bg-zinc-800 text-zinc-100"
                  }`}
                >
                  {isUser
                    ? message.content
                    : assistantPreview ??
                      (message.content ||
                        (message.status === "pending" ? "…" : ""))}
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
                      <span className="text-xs font-semibold text-slate-500">
                        {bandLabel}
                      </span>
                      {normalizedPayload.handoff && (
                        <div className="w-full rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                          <span className="font-semibold">
                            {handoffTitle(locale)}.
                          </span>{" "}
                          {handoffSubtitle({
                            handoffReason: normalizedPayload.handoff_reason,
                            confidence: Math.round(confidence * 100),
                            uiLocale: locale,
                          })}
                        </div>
                      )}
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-soft">
                      <ResponsePanel data={normalizedPayload} />
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
          />
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
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
