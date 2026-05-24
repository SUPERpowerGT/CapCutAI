import type {Message} from "../types/contracts";

export function formatTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function extractPreviewHeadline(messages: Message[]) {
  const latestAssistant = [...messages]
    .reverse()
    .find((message) => message.role === "ASSISTANT");

  if (!latestAssistant) {
    return "等待第一条 agent 回复";
  }

  return latestAssistant.content;
}

export function buildPendingUserMessage(conversationId: string, content: string): Message {
  return {
    messageId: `pending_${Date.now()}`,
    conversationId,
    role: "USER",
    content,
    status: "SUBMITTED",
    trace: [],
    createdAt: new Date().toISOString()
  };
}
