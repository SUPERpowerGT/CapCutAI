import type {KeyboardEvent} from "react";
import {buttonStyle, mutedTextStyle} from "./styles";

type ChatComposerProps = {
  prompt: string;
  isSending: boolean;
  onPromptChange: (value: string) => void;
  onSend: () => void;
};

export function ChatComposer({
  prompt,
  isSending,
  onPromptChange,
  onSend
}: ChatComposerProps) {
  const handlePromptKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };

  return (
    <div
      style={{
        padding: "14px",
        borderTop: "1px solid rgba(255,255,255,0.06)",
        background: "#13171b"
      }}
    >
      <textarea
        value={prompt}
        onChange={(event) => onPromptChange(event.target.value)}
        onKeyDown={handlePromptKeyDown}
        placeholder="输入消息，按 Enter 发送，Shift + Enter 换行"
        style={{
          width: "100%",
          minHeight: "88px",
          resize: "none",
          borderRadius: "14px",
          border: "1px solid rgba(255,255,255,0.08)",
          background: "#0f1317",
          color: "#eef2f5",
          padding: "14px",
          font: "inherit",
          outline: "none"
        }}
      />
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "12px",
          marginTop: "12px"
        }}
      >
        <p style={mutedTextStyle}>
          {isSending ? "Agent 正在处理中..." : "当前链路已经接到 backend + ai-service"}
        </p>
        <button
          style={{
            ...buttonStyle,
            opacity: !prompt.trim() || isSending ? 0.5 : 1
          }}
          disabled={!prompt.trim() || isSending}
          onClick={onSend}
        >
          Send
        </button>
      </div>
    </div>
  );
}
