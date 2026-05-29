import type {RefObject} from "react";
import type {AgentActivityItem, Message} from "../types/contracts";
import {sectionLabelStyle} from "./styles";
import {MessageFeed} from "./MessageFeed";
import {ChatComposer} from "./ChatComposer";

type ChatPanelProps = {
  messages: Message[];
  agentStatus: string;
  taskSummary: string;
  currentActivity: AgentActivityItem | null;
  prompt: string;
  error: string | null;
  isBooting: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  isStreamingAssistant: boolean;
  streamingAssistantMessage: Message | null;
  messageEndRef: RefObject<HTMLDivElement>;
  onPromptChange: (value: string) => void;
  onSend: () => void;
  onCreateConversation: () => void;
};

export function ChatPanel({
  messages,
  agentStatus,
  taskSummary,
  currentActivity,
  prompt,
  error,
  isBooting,
  isLoadingMessages,
  isSending,
  isStreamingAssistant,
  streamingAssistantMessage,
  messageEndRef,
  onPromptChange,
  onSend,
  onCreateConversation
}: ChatPanelProps) {
  return (
    <section
      style={{
        minHeight: 0,
        display: "grid",
        gridTemplateRows: "40px minmax(0, 1fr) auto",
        background: "#15181b",
        position: "relative"
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "12px",
          padding: "0 12px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          background: "#171b1f"
        }}
      >
        <div>
          <p style={sectionLabelStyle}>Agent</p>
        </div>
        <div style={{display: "flex", gap: "8px"}}>
          <button
            style={{
              appearance: "none",
              border: "1px solid rgba(255,255,255,0.08)",
              background: "#f3f5f7",
              color: "#111315",
              borderRadius: "8px",
              padding: "5px 10px",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer"
            }}
            onClick={onCreateConversation}
          >
            New
          </button>
        </div>
      </div>

      <MessageFeed
        isBooting={isBooting}
        isLoadingMessages={isLoadingMessages}
        isSending={isSending}
        isStreamingAssistant={isStreamingAssistant}
        error={error}
        messages={messages}
        currentActivity={currentActivity}
        streamingAssistantMessage={streamingAssistantMessage}
        messageEndRef={messageEndRef}
      />

      <ChatComposer
        prompt={prompt}
        isSending={isSending}
        isStreamingAssistant={isStreamingAssistant}
        onPromptChange={onPromptChange}
        onSend={onSend}
      />
    </section>
  );
}
