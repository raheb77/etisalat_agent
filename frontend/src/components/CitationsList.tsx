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
};

export function CitationsList({ citations }: CitationsListProps) {
  const citationsToRender = dedupeCitations(citations);

  if (citationsToRender.length === 0) {
    return <p className="text-sm text-slate-500">No citations returned.</p>;
  }

  return (
    <div className="space-y-3">
      {citationsToRender.map((citation, index) => (
        <div
          key={`${citation.source}-${citation.chunk_id}-${index}`}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3"
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
          <div className="text-sm font-medium text-slate-700">
            {citation.chunk_id}
          </div>
          <div className="mt-2 text-xs uppercase tracking-wide text-slate-400">
            Score
          </div>
          <div className="text-sm font-medium text-slate-700">
            {citation.score.toFixed(3)}
          </div>
        </div>
      ))}
    </div>
  );
}
