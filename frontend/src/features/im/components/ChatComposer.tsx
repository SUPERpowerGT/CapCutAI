import {useEffect, useRef} from "react";
import type {CompositionEvent, KeyboardEvent} from "react";
import {buttonStyle, mutedTextStyle} from "./styles";

type ChatComposerProps = {
  prompt: string;
  isSending: boolean;
  isStreamingAssistant: boolean;
  onPromptChange: (value: string) => void;
  onSend: () => void;
};

export function ChatComposer({
  prompt,
  isSending,
  isStreamingAssistant,
  onPromptChange,
  onSend
}: ChatComposerProps) {
  const isComposingRef = useRef(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "0px";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 220)}px`;
  }, [prompt]);

  const handleCompositionStart = () => {
    isComposingRef.current = true;
  };

  const handleCompositionEnd = (event: CompositionEvent<HTMLTextAreaElement>) => {
    isComposingRef.current = false;
    onPromptChange(event.currentTarget.value);
  };

  const handlePromptKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (isComposingRef.current || event.nativeEvent.isComposing) {
      return;
    }

    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };

  const placeholder = "描述想分析、生成或修改的内容，按 Enter 发送";

  return (
    <div
      style={{
        padding: "12px",
        borderTop: "1px solid rgba(255,255,255,0.06)",
        background: "#13171b"
      }}
    >
      <textarea
        ref={textareaRef}
        value={prompt}
        onChange={(event) => onPromptChange(event.target.value)}
        onCompositionStart={handleCompositionStart}
        onCompositionEnd={handleCompositionEnd}
        onKeyDown={handlePromptKeyDown}
        placeholder={placeholder}
        style={{
          width: "100%",
          minHeight: "72px",
          maxHeight: "220px",
          resize: "none",
          overflowY: "auto",
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
          marginTop: "10px"
        }}
      >
        <p style={mutedTextStyle}>
          {isSending
            ? "Agent 正在处理中..."
            : isStreamingAssistant
              ? "Agent 正在回复..."
              : "输入任务指令。Enter 发送，Shift + Enter 换行"}
        </p>
        <button
          style={{
            ...buttonStyle,
            padding: "9px 14px",
            opacity: !prompt.trim() || isSending || isStreamingAssistant ? 0.5 : 1
          }}
          disabled={!prompt.trim() || isSending || isStreamingAssistant}
          onClick={onSend}
        >
          Send
        </button>
      </div>
    </div>
  );
}
