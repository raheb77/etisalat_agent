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

    expect(screen.getByText(/يتطلب تحويل للموظف/i)).toBeInTheDocument();
    expect(screen.getByText(/تصنيف عالي الخطورة/i)).toBeInTheDocument();
  });
});
