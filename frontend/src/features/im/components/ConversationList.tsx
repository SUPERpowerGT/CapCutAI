import type {Conversation} from "../types/contracts";
import {formatTimestamp} from "../lib/formatters";
type ConversationListProps = {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onDeleteConversation: (conversationId: string) => void;
};

export function ConversationList({
  conversations,
  activeConversationId,
  onSelectConversation,
  onDeleteConversation
}: ConversationListProps) {
  return (
    <div
      className="conversation-tabs-scroll"
      style={{
        overflowX: "auto",
        overflowY: "hidden",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        background: "#14181c"
      }}
    >
      <div
        style={{
          display: "flex",
          gap: "0",
          minWidth: "max-content",
          paddingRight: "12px",
          alignItems: "stretch"
        }}
      >
        {conversations.map((conversation) => {
          const isActive = conversation.conversationId === activeConversationId;
          return (
            <button
              key={conversation.conversationId}
              onClick={() => onSelectConversation(conversation.conversationId)}
              style={{
                textAlign: "left",
                minWidth: "180px",
                maxWidth: "208px",
                height: "46px",
                padding: "0 10px 0 12px",
                borderRadius: 0,
                border: "none",
                borderTop: "1px solid rgba(255,255,255,0.06)",
                borderRight: "1px solid rgba(255,255,255,0.06)",
                borderBottom: isActive
                  ? "2px solid #4c8dff"
                  : "1px solid rgba(255,255,255,0.06)",
                borderLeft: "1px solid rgba(255,255,255,0.06)",
                background: isActive ? "#10151b" : "#14181d",
                color: "#eef2f5",
                cursor: "pointer",
                marginRight: "-1px",
                flex: "0 0 auto"
              }}
              title={`${conversation.title} · ${formatTimestamp(conversation.updatedAt)}`}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "10px"
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    minWidth: 0
                  }}
                >
                  <span
                    style={{
                      width: "10px",
                      height: "10px",
                      borderRadius: "999px",
                      background: isActive ? "#4c8dff" : "#4a5561",
                      flex: "0 0 auto"
                    }}
                  />
                  <div style={{minWidth: 0}}>
                    <div
                      style={{
                        fontSize: "13px",
                        fontWeight: 600,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis"
                      }}
                    >
                      {conversation.title}
                    </div>
                  </div>
                </div>
                <span
                  onClick={(event) => {
                    event.stopPropagation();
                    onDeleteConversation(conversation.conversationId);
                  }}
                  style={{
                    color: "#8d96a0",
                    fontSize: "14px",
                    lineHeight: 1,
                    flex: "0 0 auto",
                    cursor: "pointer",
                    width: "18px",
                    height: "18px",
                    display: "grid",
                    placeItems: "center",
                    borderRadius: "999px",
                    background: isActive ? "rgba(255,255,255,0.04)" : "transparent"
                  }}
                >
                  ×
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
