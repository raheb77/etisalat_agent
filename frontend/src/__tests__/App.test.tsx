import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { App } from "../App";

vi.mock("../hooks/useChat", () => ({
  useChat: () => ({
    messages: [],
    isLoading: false,
    error: "RATE_LIMIT",
    sendMessage: vi.fn(),
    clearMessages: vi.fn(),
  }),
}));

describe("App error handling", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true })) as unknown as typeof fetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders rate limit error UI when error_code=RATE_LIMIT", async () => {
    render(<App />);
    expect(await screen.findByText("RATE_LIMIT")).toBeInTheDocument();
  });
});
