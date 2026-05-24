import type {RefObject} from "react";
import type {Conversation, Message} from "../types/contracts";
import {buttonStyle, mutedTextStyle, sectionLabelStyle} from "./styles";
import {ConversationList} from "./ConversationList";
import {MessageFeed} from "./MessageFeed";
import {ChatComposer} from "./ChatComposer";

type ChatPanelProps = {
  activeConversation: Conversation | null;
  activeConversationId: string | null;
  conversations: Conversation[];
  messages: Message[];
  prompt: string;
  error: string | null;
  isBooting: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  messageEndRef: RefObject<HTMLDivElement>;
  onPromptChange: (value: string) => void;
  onSend: () => void;
  onSelectConversation: (conversationId: string) => void;
  onDeleteConversation: (conversationId: string) => void;
  onRefresh: () => void;
  onCreateConversation: () => void;
};

export function ChatPanel({
  activeConversation,
  activeConversationId,
  conversations,
  messages,
  prompt,
  error,
  isBooting,
  isLoadingMessages,
  isSending,
  messageEndRef,
  onPromptChange,
  onSend,
  onSelectConversation,
  onDeleteConversation,
  onRefresh,
  onCreateConversation
}: ChatPanelProps) {
  return (
    <section
      style={{
        minHeight: 0,
        display: "grid",
        gridTemplateRows: "48px 42px minmax(0, 1fr) auto",
        background: "#15181b"
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "12px",
          padding: "0 14px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          background: "#171b1f"
        }}
      >
        <div>
          <p style={sectionLabelStyle}>
            {activeConversation?.title ?? "Chat"}
          </p>
        </div>
        <div style={{display: "flex", gap: "8px"}}>
          <button
            style={{
              ...buttonStyle,
              background: "#171b1f",
              color: "#f3f5f7",
              padding: "8px 12px"
            }}
            onClick={onRefresh}
          >
            Refresh
          </button>
          <button style={{...buttonStyle, padding: "8px 12px"}} onClick={onCreateConversation}>
            New
          </button>
        </div>
      </div>

      <ConversationList
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={onSelectConversation}
        onDeleteConversation={onDeleteConversation}
      />

      <MessageFeed
        isBooting={isBooting}
        isLoadingMessages={isLoadingMessages}
        isSending={isSending}
        error={error}
        messages={messages}
        messageEndRef={messageEndRef}
      />

      <ChatComposer
        prompt={prompt}
        isSending={isSending}
        onPromptChange={onPromptChange}
        onSend={onSend}
      />
    </section>
  );
}
