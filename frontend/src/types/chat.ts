export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "pending" | "streaming" | "done" | "error";
  timestamp: number;
};

export type ChatState = {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
};
