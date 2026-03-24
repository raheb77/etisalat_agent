import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import type { Message } from "../types/chat";
import { ChatWindow } from "../components/ChatWindow";
import { responseWithHandoff } from "./fixtures";

describe("ChatWindow", () => {
  it("renders handoff banner with localized reason when handoff=true", () => {
    const messages: Message[] = [
      {
        id: "assistant-1",
        role: "assistant",
        content: responseWithHandoff.answer,
        status: "done",
        payload: responseWithHandoff,
      },
    ];

    render(
      <ChatWindow
        messages={messages}
        isLoading={false}
        onSend={vi.fn()}
        locale="ar-SA"
        onLocaleChange={vi.fn()}
        categoryHint=""
        onCategoryHintChange={vi.fn()}
      />
    );

    const handoffBanner = screen.getByTestId("handoff-banner");
    expect(handoffBanner).toBeInTheDocument();
    expect(handoffBanner).toHaveTextContent(/يتطلب تحويل للموظف/i);
    expect(handoffBanner).toHaveTextContent(/تصنيف عالي الخطورة/i);
  });
});
