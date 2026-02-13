export const API_BASE =
  import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8001";

type QueryAgentParams = {
  question: string;
  locale?: string;
  channel?: string;
  category_hint?: string;
};

export async function queryAgent(
  params: QueryAgentParams,
  signal?: AbortSignal
) {
  const { question, category_hint } = params;
  const locale = params.locale ?? "ar-SA";
  const channel = params.channel ?? "csr_ui";
  const body = {
    question,
    locale,
    channel,
    ...(category_hint ? { category_hint } : {}),
  };

  const response = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed (${response.status}).`);
  }

  return response.json();
}
