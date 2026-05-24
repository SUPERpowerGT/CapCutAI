import type {RefObject} from "react";
import {formatTimestamp} from "../lib/formatters";
import type {Message} from "../types/contracts";
import {mutedTextStyle, roleStyleMap} from "./styles";

type MessageFeedProps = {
  isBooting: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  error: string | null;
  messages: Message[];
  messageEndRef: RefObject<HTMLDivElement>;
};

export function MessageFeed({
  isBooting,
  isLoadingMessages,
  isSending,
  error,
  messages,
  messageEndRef
}: MessageFeedProps) {
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
            padding: "16px",
            borderRadius: "14px",
            background: "#111418",
            border: "1px dashed rgba(255,255,255,0.08)",
            color: "#aeb8c1",
            fontSize: "13px"
          }}
        >
          No messages yet. Send the first prompt to start the scaffold flow.
        </div>
      ) : null}

      {messages.map((message) => (
        <article
          key={message.messageId}
          style={{
            maxWidth: "92%",
            padding: "14px",
            borderRadius: "14px",
            display: "grid",
            gap: "10px",
            ...roleStyleMap[message.role]
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "12px",
              fontSize: "11px",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "#95a0ab"
            }}
          >
            <span>{message.role}</span>
            <span>{formatTimestamp(message.createdAt)}</span>
          </div>
          <div style={{fontSize: "14px", lineHeight: 1.6}}>{message.content}</div>
        </article>
      ))}

      {isSending ? (
        <div
          style={{
            maxWidth: "92%",
            padding: "14px",
            borderRadius: "14px",
            background: "#161a1f",
            border: "1px solid rgba(255,255,255,0.05)"
          }}
        >
          <div style={{fontSize: "13px", color: "#a8b2bb"}}>Thinking...</div>
        </div>
      ) : null}

      <div ref={messageEndRef} />
    </div>
  );
}
