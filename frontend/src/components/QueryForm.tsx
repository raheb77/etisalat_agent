import type { FormEvent } from "react";

export type StatusTone = "idle" | "loading" | "success" | "error";

type QueryFormProps = {
  question: string;
  categoryHint: string;
  locale: string;
  apiBase: string;
  onQuestionChange: (value: string) => void;
  onCategoryHintChange: (value: string) => void;
  onLocaleChange: (value: string) => void;
  onApiBaseChange: (value: string) => void;
  onSubmit: () => void;
  onSample: () => void;
  isLoading: boolean;
  statusMessage: string;
  statusTone: StatusTone;
};

const toneClass: Record<StatusTone, string> = {
  idle: "text-slate-500",
  loading: "text-amber-700",
  success: "text-emerald-700",
  error: "text-rose-700",
};

export function QueryForm({
  question,
  categoryHint,
  locale,
  apiBase,
  onQuestionChange,
  onCategoryHintChange,
  onLocaleChange,
  onApiBaseChange,
  onSubmit,
  onSample,
  isLoading,
  statusMessage,
  statusTone,
}: QueryFormProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex h-full flex-col gap-6"
      noValidate
    >
      <div className="space-y-2">
        <label className="text-sm font-semibold text-slate-800" htmlFor="question">
          Question
        </label>
        <textarea
          id="question"
          name="question"
          rows={6}
          className="w-full rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-sm shadow-sm outline-none transition focus:border-teal-500 focus:ring-4 focus:ring-teal-200"
          placeholder="Ask a CSR policy or plan question..."
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          required
        />
        <p className="text-xs text-slate-500">No PII. Keep it short and precise.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label
            className="text-sm font-semibold text-slate-800"
            htmlFor="categoryHint"
          >
            Category hint
          </label>
          <input
            id="categoryHint"
            name="categoryHint"
            type="text"
            className="w-full rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-sm shadow-sm outline-none transition focus:border-teal-500 focus:ring-4 focus:ring-teal-200"
            placeholder="billing, network, plans"
            value={categoryHint}
            onChange={(event) => onCategoryHintChange(event.target.value)}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-slate-800" htmlFor="locale">
            Locale
          </label>
          <select
            id="locale"
            name="locale"
            className="w-full rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-sm shadow-sm outline-none transition focus:border-teal-500 focus:ring-4 focus:ring-teal-200"
            value={locale}
            onChange={(event) => onLocaleChange(event.target.value)}
          >
            <option value="ar-SA">ar-SA</option>
            <option value="en-US">en-US</option>
          </select>
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-semibold text-slate-800" htmlFor="apiBase">
          API base URL
        </label>
        <input
          id="apiBase"
          name="apiBase"
          type="url"
          className="w-full rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-sm shadow-sm outline-none transition focus:border-teal-500 focus:ring-4 focus:ring-teal-200"
          placeholder="http://localhost:8000"
          value={apiBase}
          onChange={(event) => onApiBaseChange(event.target.value)}
        />
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          className="rounded-full bg-teal-700 px-6 py-3 text-sm font-semibold text-white shadow-soft transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isLoading}
        >
          Run query
        </button>
        <button
          type="button"
          className="rounded-full bg-orange-100 px-6 py-3 text-sm font-semibold text-orange-700 transition hover:-translate-y-0.5"
          onClick={onSample}
        >
          Use sample
        </button>
      </div>

      <div className={`min-h-[1.2rem] text-sm ${toneClass[statusTone]}`}>
        {statusMessage}
      </div>
    </form>
  );
}
