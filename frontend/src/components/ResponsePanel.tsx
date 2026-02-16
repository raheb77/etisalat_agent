import type { QueryResponse } from "../types/query";
import { CitationsList } from "./CitationsList";

const formatPercent = (value: number) => `${Math.round(value * 100)}%`;

type ResponsePanelProps = {
  data: QueryResponse | null;
  uiLocale?: "ar-SA" | "en-US";
};

export function ResponsePanel({ data, uiLocale }: ResponsePanelProps) {
  if (!data) {
    return (
      <div className="text-center text-slate-500">
        <h2 className="font-display text-2xl text-slate-700">
          Response preview
        </h2>
        <p className="mt-2 text-sm">
          Submit a query to see the answer, confidence, and citations.
        </p>
      </div>
    );
  }

  const steps = data.steps ?? [];
  const confidence = Number.isFinite(data.confidence) ? data.confidence : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display text-2xl text-slate-800">Answer</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-700">
          {data.answer}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <div className="text-xs uppercase tracking-wide text-slate-400">
            Confidence
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-teal-100">
            <div
              className="h-full rounded-full bg-gradient-to-r from-teal-600 via-teal-400 to-amber-400"
              style={{ width: formatPercent(confidence) }}
            />
          </div>
          <div className="mt-2 text-sm font-semibold text-slate-700">
            {formatPercent(confidence)}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <div className="text-xs uppercase tracking-wide text-slate-400">
            Category
          </div>
          <div className="mt-2 inline-flex rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-800">
            {data.category || "Unknown"}
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <div className="text-xs uppercase tracking-wide text-slate-400">
            Handoff
          </div>
          <div className="mt-2 inline-flex rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-700">
            {data.handoff ? "Yes" : "No"}
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <div className="text-xs uppercase tracking-wide text-slate-400">
            Reason
          </div>
          <div className="mt-2 text-sm font-medium text-slate-700">
            {data.handoff_reason || "-"}
          </div>
        </div>
      </div>

      {steps.length > 0 && (
        <div>
          <h2 className="font-display text-2xl text-slate-800">Steps</h2>
          <ul className="mt-3 space-y-2">
            {steps.map((step, index) => (
              <li
                key={`${step}-${index}`}
                className="rounded-xl bg-teal-50 px-4 py-2 text-sm text-slate-700"
              >
                {step}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <h2 className="font-display text-2xl text-slate-800">Citations</h2>
        <div className="mt-3">
          <CitationsList citations={data.citations ?? []} uiLocale={uiLocale} />
        </div>
      </div>
    </div>
  );
}
