export type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type Conversation = {
  conversationId: string;
  userId: string;
  sessionId: string;
  title: string;
  status: string;
  createdAt: string;
  updatedAt: string;
};

export type Message = {
  messageId: string;
  conversationId: string;
  role: "SYSTEM" | "USER" | "ASSISTANT";
  content: string;
  status: string;
  trace: string[];
  createdAt: string;
};

export type SendMessageResult = {
  conversationId: string;
  userMessage: Message;
  assistantMessage: Message;
  agentStatus: string;
};
