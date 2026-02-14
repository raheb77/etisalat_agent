import { useCallback, useRef, useState } from "react";

import { queryAgent } from "../config/api";
import type { Message, ChatState } from "../types/chat";
import type { QueryResponse } from "../types/query";

type UseChatResult = ChatState & {
  error: string | null;
  sendMessage: (
    question: string,
    options?: {
      locale?: string;
      channel?: string;
      category_hint?: string;
    }
  ) => Promise<void>;
  clearMessages: () => void;
};

export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestRef = useRef<AbortController | null>(null);

  const updateMessageById = useCallback(
    (id: string, patch: Partial<Message>) => {
      setMessages((prev) =>
        prev.map((message) =>
          message.id === id ? { ...message, ...patch } : message
        )
      );
    },
    []
  );

  const sendMessage = useCallback(
    async (
      question: string,
      options?: { locale?: string; channel?: string; category_hint?: string }
    ) => {
      const trimmed = question.trim();
      if (!trimmed) {
        setError("Message cannot be empty.");
        return;
      }

      if (requestRef.current) {
        requestRef.current.abort();
      }
      const controller = new AbortController();
      requestRef.current = controller;

      setError(null);
      const assistantId = crypto.randomUUID();
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
        status: "done",
      };
      const assistantMessage: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        status: "pending",
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsLoading(true);

      try {
        const data = (await queryAgent({
          question: trimmed,
          locale: options?.locale ?? "ar-SA",
          channel: options?.channel ?? "csr_ui",
          ...(options?.category_hint
            ? { category_hint: options.category_hint }
            : {}),
        }, controller.signal)) as QueryResponse;

        if (controller.signal.aborted || requestRef.current !== controller) {
          return;
        }

        updateMessageById(assistantId, {
          content: data.answer ?? "",
          payload: data,
          status: "done",
        });
      } catch (err) {
        if (controller.signal.aborted || requestRef.current !== controller) {
          return;
        }
        const message = err instanceof Error ? err.message : "Unexpected error";
        updateMessageById(assistantId, {
          content: message,
          status: "error",
        });
        setError(message);
      } finally {
        if (requestRef.current === controller) {
          requestRef.current = null;
          setIsLoading(false);
        }
      }
    },
    [updateMessageById]
  );

  const clearMessages = useCallback(() => {
    if (requestRef.current) {
      requestRef.current.abort();
      requestRef.current = null;
    }
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
