import type {RefObject} from "react";
import type {AgentActivityItem, AgentArtifacts, Message} from "../types/contracts";
import {sectionLabelStyle} from "./styles";
import {MessageFeed} from "./MessageFeed";
import {ChatComposer} from "./ChatComposer";

type ChatPanelProps = {
  messages: Message[];
  messageArtifacts: Record<string, AgentArtifacts>;
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
};

export function ChatPanel({
  messages,
  messageArtifacts,
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
  onSend
}: ChatPanelProps) {
  return (
    <section
      style={{
        minHeight: 0,
        minWidth: 0,
        display: "grid",
        gridTemplateRows: "56px minmax(0, 1fr) auto",
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
          padding: "0 16px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          background: "#171b1f"
        }}
      >
        <div>
          <p style={sectionLabelStyle}>Agent</p>
        </div>
        <div />
      </div>

      <MessageFeed
        isBooting={isBooting}
        isLoadingMessages={isLoadingMessages}
        isSending={isSending}
        isStreamingAssistant={isStreamingAssistant}
        error={error}
        messages={messages}
        messageArtifacts={messageArtifacts}
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
