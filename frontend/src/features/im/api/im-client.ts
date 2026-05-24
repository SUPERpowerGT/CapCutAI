import type {
  ApiResponse,
  Conversation,
  Message,
  SendMessageResult
} from "../types/contracts";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  const body = (await response.json()) as ApiResponse<T>;
  if (body.code !== 0) {
    throw new Error(body.message);
  }

  return body.data;
}

export function listConversations() {
  return request<Conversation[]>("/api/im/conversations");
}

export function createConversation(title?: string) {
  return request<Conversation>("/api/im/conversations", {
    method: "POST",
    body: JSON.stringify({title})
  });
}

export function deleteConversation(conversationId: string) {
  return request<void>(`/api/im/conversations/${conversationId}`, {
    method: "DELETE"
  });
}

export function listMessages(conversationId: string) {
  return request<Message[]>(`/api/im/conversations/${conversationId}/messages`);
}

export function sendMessage(conversationId: string, content: string) {
  return request<SendMessageResult>(`/api/im/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({content})
  });
}
