import type { Citation } from "../types/query";

type CitationsListProps = {
  citations: Citation[];
};

export function CitationsList({ citations }: CitationsListProps) {
  if (citations.length === 0) {
    return <p className="text-sm text-slate-500">No citations returned.</p>;
  }

  return (
    <div className="space-y-3">
      {citations.map((citation, index) => (
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
