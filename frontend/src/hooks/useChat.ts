import { useCallback, useState } from "react";

import { queryAgent } from "../config/api";
import type { Message, ChatState } from "../types/chat";
import type { QueryResponse } from "../types/query";

type UseChatResult = ChatState & {
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
};

export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateLastAssistantMessage = useCallback(
    (updates: Partial<Message>) => {
      setMessages((prev) => {
        const lastIndex = [...prev]
          .reverse()
          .findIndex((message) => message.role === "assistant");
        if (lastIndex === -1) {
          return prev;
        }
        const targetIndex = prev.length - 1 - lastIndex;
        const next = [...prev];
        next[targetIndex] = { ...next[targetIndex], ...updates };
        return next;
      });
    },
    []
  );

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed) {
        setError("Message cannot be empty.");
        return;
      }

      setError(null);
      const timestamp = Date.now();
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
        status: "done",
        timestamp,
      };
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "",
        status: "pending",
        timestamp,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsLoading(true);

      try {
        const data = (await queryAgent({
          question: trimmed,
          locale: "ar-SA",
          channel: "csr_ui",
        })) as QueryResponse;
        updateLastAssistantMessage({
          content: data.answer ?? "",
          status: "done",
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unexpected error";
        updateLastAssistantMessage({
          content: message,
          status: "error",
        });
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [updateLastAssistantMessage]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setIsLoading(false);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  };
}
