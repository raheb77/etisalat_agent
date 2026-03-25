import { useState } from "react";

import type { Citation } from "../types/query";
import { computeEvidenceLevel, getEvidenceLabel } from "../utils/evidence";

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

function toReadableSegment(value: string): string {
  return value
    .replace(/\.[^.]+$/, "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function formatCitationSourceLabel(source: string): string {
  const trimmed = source.trim();
  if (!trimmed) return "Unknown source";

  const parts = trimmed.split("/").filter(Boolean);
const filename = parts[parts.length - 1] ?? trimmed;

if (/^compass_artifact_/i.test(filename)) {
  return "Compass artifact";
}

const readableFile = toReadableSegment(filename);
const parent = parts.length > 1 ? parts[parts.length - 2] : undefined;
if (!parent) return readableFile;

  const readableParent = toReadableSegment(parent);
  if (!readableParent || readableParent === readableFile) {
    return readableFile;
  }

  return `${readableParent} / ${readableFile}`;
}

export function CitationsList({ citations, uiLocale = "en-US" }: CitationsListProps) {
  const citationsToRender = dedupeCitations(citations);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const toggle = (key: string) =>
    setExpanded((state) => ({ ...state, [key]: !state[key] }));
  const evidenceLevel = computeEvidenceLevel(citationsToRender);
  const evidenceLabel = getEvidenceLabel(evidenceLevel, uiLocale);

  const showLabel = uiLocale === "ar-SA" ? "عرض" : "Show";
  const hideLabel = uiLocale === "ar-SA" ? "إخفاء" : "Hide";
  const evidencePrefix = uiLocale === "ar-SA" ? "الأدلة:" : "Evidence:";
  const valueDir = uiLocale === "ar-SA" ? "rtl" : "ltr";

  return (
    <div className="space-y-2.5" data-testid="citations-list">
      <div className="text-sm text-slate-500">
        {evidencePrefix} {evidenceLabel}
      </div>
      {citationsToRender.length === 0 && (
        <p className="text-sm text-slate-500">No citations returned.</p>
      )}
      {citationsToRender.map((citation, index) => {
        const key = citationKey(citation);
        const sourceLabel = formatCitationSourceLabel(citation.source);
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
            className="rounded-lg border border-zinc-200/70 px-3 py-2 transition-all duration-150 hover:border-blue-300 hover:bg-blue-50/40 focus-within:ring-2 focus-within:ring-blue-500"
          >
            <div className="flex items-start gap-3" dir="ltr">
              <div className="w-14 shrink-0 pt-0.5 text-[11px] uppercase tracking-wide text-slate-400">
                Source
              </div>
              <div
                className="min-w-0 flex-1 text-start text-sm font-medium leading-5 text-slate-700"
                title={citation.source}
                dir={valueDir}
              >
                {sourceLabel}
              </div>
            </div>
            <div className="mt-1.5 flex items-start gap-3" dir="ltr">
              <div className="w-14 shrink-0 pt-0.5 text-[11px] uppercase tracking-wide text-slate-400">
                Chunk
              </div>
              <div className="min-w-0 flex-1 text-start" dir={valueDir}>
                <div
                  id={controlsId}
                  className="text-sm font-medium leading-5 text-slate-700 whitespace-pre-wrap break-words"
                >
                  {displayText}
                </div>
                <button
                  type="button"
                  className="mt-1 text-[11px] font-semibold text-blue-600 hover:text-blue-700"
                  aria-expanded={isExpanded}
                  aria-controls={controlsId}
                  onClick={() => toggle(key)}
                >
                  {isExpanded ? hideLabel : showLabel}
                </button>
              </div>
            </div>
            <div className="mt-1.5 flex items-center gap-3" dir="ltr">
              <div className="w-14 shrink-0 text-[11px] uppercase tracking-wide text-slate-400">
                Score
              </div>
              <div
                className="text-start text-sm font-medium leading-5 text-slate-700"
                dir={valueDir}
              >
                {citation.score.toFixed(3)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
