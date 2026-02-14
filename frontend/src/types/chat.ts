import type { QueryResponse } from "./query";

export type Role = "user" | "assistant";

export type MessageStatus = "pending" | "done" | "error";

export interface Message {
  id: string;
  role: Role;
  content: string;
  status: MessageStatus;
  payload?: QueryResponse;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
}
