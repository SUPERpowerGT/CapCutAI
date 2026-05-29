import type {RefObject} from "react";
import type {AgentActivityItem, Message} from "../types/contracts";
import {mutedTextStyle, roleStyleMap} from "./styles";
import {ActivityFeedItem} from "./ActivityFeedItem";

type MessageFeedProps = {
  isBooting: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  isStreamingAssistant: boolean;
  error: string | null;
  messages: Message[];
  currentActivity: AgentActivityItem | null;
  streamingAssistantMessage: Message | null;
  messageEndRef: RefObject<HTMLDivElement>;
};

export function MessageFeed({
  isBooting,
  isLoadingMessages,
  isSending,
  isStreamingAssistant,
  error,
  messages,
  currentActivity,
  streamingAssistantMessage,
  messageEndRef
}: MessageFeedProps) {
  const showInlineActivity = currentActivity && !streamingAssistantMessage;

  return (
    <div
      style={{
        minHeight: 0,
        overflow: "auto",
        padding: "16px",
        display: "grid",
        alignContent: "start",
        gap: "12px"
      }}
    >
      {isBooting ? <p style={mutedTextStyle}>Booting scaffold...</p> : null}
      {!isBooting && isLoadingMessages ? <p style={mutedTextStyle}>Loading messages...</p> : null}

      {error ? (
        <div
          style={{
            padding: "12px",
            borderRadius: "12px",
            background: "#2a1717",
            border: "1px solid rgba(255,130,130,0.25)",
            color: "#ffd4d4",
            fontSize: "13px"
          }}
        >
          {error}
        </div>
      ) : null}

      {!isBooting && !isLoadingMessages && messages.length === 0 ? (
        <div
          style={{
            padding: "18px",
            borderRadius: "14px",
            background: "#111418",
            border: "1px dashed rgba(255,255,255,0.08)",
            color: "#aeb8c1",
            fontSize: "13px",
            lineHeight: 1.6
          }}
        >
          这里还没有消息。发第一条指令开始当前对话。
        </div>
      ) : null}

      {messages.map((message) => (
        <article
          key={message.messageId}
          style={{
            maxWidth: message.role === "ASSISTANT" ? "100%" : "92%",
            padding: message.role === "ASSISTANT" ? "2px 0 6px" : "12px 14px",
            borderRadius: message.role === "ASSISTANT" ? "0" : "14px",
            display: "grid",
            gap: "8px",
            ...roleStyleMap[message.role]
          }}
        >
          <div
            style={{
              fontSize: "14px",
              lineHeight: message.role === "ASSISTANT" ? 1.75 : 1.6,
              color: message.role === "ASSISTANT" ? "#edf2f7" : undefined,
              paddingRight: message.role === "ASSISTANT" ? "8px" : undefined
            }}
          >
            {message.content}
          </div>
        </article>
      ))}

      {streamingAssistantMessage ? (
        <article
          style={{
            maxWidth: "100%",
            padding: "2px 0 6px",
            borderRadius: "0",
            display: "grid",
            gap: "10px",
            ...roleStyleMap.ASSISTANT
          }}
        >
          <div
            style={{
              fontSize: "14px",
              lineHeight: 1.75,
              color: "#edf2f7",
              paddingRight: "8px"
            }}
          >
            {streamingAssistantMessage.content || " "}
            {isStreamingAssistant ? (
              <span className="agent-stream-caret" />
            ) : null}
          </div>
        </article>
      ) : null}

      {showInlineActivity ? <ActivityFeedItem activity={currentActivity} /> : null}

      <div ref={messageEndRef} />
    </div>
  );
}
