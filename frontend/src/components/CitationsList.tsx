import { useState } from "react";

import type { Citation } from "../types/query";

function citationKey(c: any): string {
  const sourceRaw = c?.source ?? "unknown";
  const source = typeof sourceRaw === "string" ? sourceRaw.trim() : String(sourceRaw);

  const chunk = typeof c?.chunk === "string" ? c.chunk.trim() : "";
  if (chunk) return `${source}::chunk:${chunk}`;

  const chunkId = typeof c?.chunk_id === "string" ? c.chunk_id.trim() : "";
  if (chunkId) return `${source}::id:${chunkId}`;

  try {
    return `${source}::json:${JSON.stringify(c?.chunk ?? c ?? null)}`;
  } catch {
    return `${source}::fallback:${String(c?.chunk ?? c ?? "")}`;
  }
}

function dedupeCitations<T extends { score?: number }>(items: T[]): T[] {
  if (!items?.length) return [];
  const seen = new Map<string, { item: T; firstIndex: number }>();

  items.forEach((item, index) => {
    const key = citationKey(item);
    const existing = seen.get(key);

    if (!existing) {
      seen.set(key, { item, firstIndex: index });
      return;
    }

    const sNew = item.score ?? 0;
    const sOld = existing.item.score ?? 0;

    if (sNew > sOld) {
      seen.set(key, { item, firstIndex: existing.firstIndex });
    }
  });

  return Array.from(seen.values())
    .sort((a, b) => a.firstIndex - b.firstIndex)
    .map((x) => x.item);
}

type CitationsListProps = {
  citations: Citation[];
  uiLocale?: "ar-SA" | "en-US";
};

const PREVIEW_MAX = 150;
const EXPANDED_MAX = 500;

function truncateChunk(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  return `${text.slice(0, maxChars)}…`;
}

export function CitationsList({ citations, uiLocale = "en-US" }: CitationsListProps) {
  const citationsToRender = dedupeCitations(citations);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const toggle = (key: string) =>
    setExpanded((state) => ({ ...state, [key]: !state[key] }));

  if (citationsToRender.length === 0) {
    return <p className="text-sm text-slate-500">No citations returned.</p>;
  }

  const showLabel = uiLocale === "ar-SA" ? "عرض" : "Show";
  const hideLabel = uiLocale === "ar-SA" ? "إخفاء" : "Hide";

  return (
    <div className="space-y-3">
      {citationsToRender.map((citation, index) => {
        const key = citationKey(citation);
        const rawChunk = (citation as { chunk?: unknown }).chunk;
        const chunkText =
          typeof rawChunk === "string"
            ? rawChunk.trim()
            : typeof citation.chunk_id === "string"
            ? citation.chunk_id.trim()
            : "";
        const isExpanded = expanded[key] === true;
        const displayText = truncateChunk(
          chunkText,
          isExpanded ? EXPANDED_MAX : PREVIEW_MAX
        );
        const controlsId = `citation-chunk-${index}`;

        return (
          <div
            key={key}
            className="p-3 rounded-lg border transition-all duration-150 border-zinc-200/70 hover:border-blue-300 hover:bg-blue-50/40 focus-within:ring-2 focus-within:ring-blue-500"
          >
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Source
            </div>
            <div className="text-sm font-medium text-slate-700">
              {citation.source}
            </div>
            <div className="mt-2 text-xs uppercase tracking-wide text-slate-400">
              Chunk
            </div>
            <div
              id={controlsId}
              className="text-sm font-medium text-slate-700 whitespace-pre-wrap break-words"
            >
              {displayText}
            </div>
            <button
              type="button"
              className="mt-2 text-xs font-semibold text-blue-600 hover:text-blue-700"
              aria-expanded={isExpanded}
              aria-controls={controlsId}
              onClick={() => toggle(key)}
            >
              {isExpanded ? hideLabel : showLabel}
            </button>
            <div className="mt-2 text-xs uppercase tracking-wide text-slate-400">
              Score
            </div>
            <div className="text-sm font-medium text-slate-700">
              {citation.score.toFixed(3)}
            </div>
          </div>
        );
      })}
    </div>
  );
}
