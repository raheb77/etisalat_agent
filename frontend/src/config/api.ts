export const API_BASE =
  import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8001";

export async function queryAgent(message: string, signal?: AbortSignal) {
  const response = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
    signal,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed (${response.status}).`);
  }

  return response.json();
}
