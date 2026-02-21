import { useEffect, useState } from "react";

import { API_BASE } from "./config/api";
import { ChatWindow } from "./components/ChatWindow";
import { useChat } from "./hooks/useChat";

const DEFAULT_LOCALE = "ar-SA";

export function App() {
  const [categoryHint, setCategoryHint] = useState("");
  const [locale, setLocale] = useState<"ar-SA" | "en-US">(DEFAULT_LOCALE);
  const [backendStatus, setBackendStatus] = useState("Checking...");

  const { messages, isLoading, error, sendMessage } = useChat();

  useEffect(() => {
    let active = true;

    const pingBackend = async () => {
      try {
        const response = await fetch(`${API_BASE}/health`);
        if (!active) return;
        setBackendStatus(response.ok ? "Online" : "Degraded");
      } catch (error) {
        if (!active) return;
        setBackendStatus("Offline");
      }
    };

    setBackendStatus("Checking...");
    pingBackend();

    return () => {
      active = false;
    };
  }, []);

  const handleSend = async (content: string) => {
    await sendMessage(content, {
      locale,
      channel: "csr_ui",
      ...(categoryHint.trim() ? { category_hint: categoryHint.trim() } : {}),
    });
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_#ffffff_0%,_#f7f3ee_45%),radial-gradient(circle_at_30%_20%,_#f1e7da_0,_transparent_55%)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-12">
        <header className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <div className="inline-flex rounded-full bg-teal-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-teal-700">
              Phase 3 UI
            </div>
            <h1 className="mt-3 font-display text-4xl text-slate-900">
              CSR Decision Support
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-relaxed text-slate-600">
              Minimal, portfolio-ready console for querying the CSR backend and
              surfacing answers with traceable citations.
            </p>
          </div>

          <div className="grid gap-3">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-soft">
              <div className="text-xs uppercase tracking-wide text-slate-400">
                Backend
              </div>
              <div className="text-sm font-semibold text-slate-700">
                {backendStatus}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-soft">
              <div className="text-xs uppercase tracking-wide text-slate-400">
                Channel
              </div>
              <div className="text-sm font-semibold text-slate-700">csr_ui</div>
            </div>
          </div>
        </header>

        <main className="grid gap-6">
          <section className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-soft">
            <ChatWindow
              messages={messages}
              isLoading={isLoading}
              onSend={handleSend}
              locale={locale}
              onLocaleChange={setLocale}
              categoryHint={categoryHint}
              onCategoryHintChange={setCategoryHint}
            />
            {error && (
              <div className="mt-4 text-sm text-rose-600" data-testid="error-banner">
                {error}
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}
