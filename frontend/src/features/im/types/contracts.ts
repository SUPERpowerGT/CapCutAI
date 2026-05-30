export type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type Conversation = {
  conversationId: string;
  userId: string;
  sessionId: string;
  workspaceId: string;
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

export type AgentActivityKind = "STATUS" | "TOOL" | "SUBAGENT" | "SYSTEM";

export type AgentActivityState =
  | "IDLE"
  | "THINKING"
  | "STREAMING"
  | "COMPLETED"
  | "FAILED";

export type AgentActivityItem = {
  id: string;
  kind: AgentActivityKind;
  state: AgentActivityState;
  title: string;
  detail: string;
  source?: string;
};

export type SendMessageResult = {
  conversationId: string;
  userMessage: Message;
  assistantMessage: Message;
  agentStatus: string;
};
