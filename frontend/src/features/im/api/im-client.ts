import type {
  AgentWorkspaceContext,
  ApiResponse,
  Conversation,
  Message,
  SendMessageResult
} from "../types/contracts";

const transport = process.env.NEXT_PUBLIC_IM_TRANSPORT ?? "proxy";
const backendBaseUrl = (
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL ?? "http://127.0.0.1:38080"
).replace(/\/$/, "");

function buildApiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  if (transport === "direct") {
    return `${backendBaseUrl}/api${normalizedPath}`;
  }

  return `/api/im${normalizedPath}`;
}

function withWorkspaceQuery(path: string, workspaceId?: string) {
  if (!workspaceId) {
    return path;
  }

  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}workspaceId=${encodeURIComponent(workspaceId)}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
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

export function listConversations(workspaceId?: string) {
  return request<Conversation[]>(withWorkspaceQuery("/conversations", workspaceId));
}

export function createConversation({
  title,
  workspaceId
}: {
  title?: string;
  workspaceId?: string;
}) {
  return request<Conversation>("/conversations", {
    method: "POST",
    body: JSON.stringify({title, workspaceId})
  });
}

export function deleteConversation(conversationId: string) {
  return request<void>(`/conversations/${conversationId}`, {
    method: "DELETE"
  });
}

export function listMessages(conversationId: string) {
  return request<Message[]>(`/conversations/${conversationId}/messages`);
}

export function sendMessage(
  conversationId: string,
  content: string,
  context?: AgentWorkspaceContext | null
) {
  return request<SendMessageResult>(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({content, context})
  });
}
