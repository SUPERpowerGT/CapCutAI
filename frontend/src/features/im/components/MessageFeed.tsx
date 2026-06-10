import type {ReactNode, RefObject} from "react";
import type {AgentActivityItem, AgentArtifacts, Message} from "../types/contracts";
import {mutedTextStyle, roleStyleMap} from "./styles";
import {ActivityFeedItem} from "./ActivityFeedItem";
import {fontFamilyMono, textStyles} from "../../../shared/design/typography";

type MessageFeedProps = {
  isBooting: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  isStreamingAssistant: boolean;
  error: string | null;
  messages: Message[];
  messageArtifacts: Record<string, AgentArtifacts>;
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
  messageArtifacts,
  currentActivity,
  streamingAssistantMessage,
  messageEndRef
}: MessageFeedProps) {
  const showInlineActivity = currentActivity && !streamingAssistantMessage;

  return (
    <div
      style={{
        minHeight: 0,
        minWidth: 0,
        maxWidth: "100%",
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
            ...textStyles.titleSmall,
            padding: "12px",
            borderRadius: "12px",
            background: "#2a1717",
            border: "1px solid rgba(255,130,130,0.25)",
            color: "#ffd4d4"
          }}
        >
          {error}
        </div>
      ) : null}

      {!isBooting && !isLoadingMessages && messages.length === 0 ? (
        <div
          style={{
            ...textStyles.titleSmall,
            padding: "18px",
            borderRadius: "14px",
            background: "#111418",
            border: "1px dashed rgba(255,255,255,0.08)",
            color: "#aeb8c1",
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
            width: "100%",
            minWidth: 0,
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
              ...textStyles.body,
              minWidth: 0,
              maxWidth: "100%",
              overflowWrap: "anywhere",
              whiteSpace: "pre-line",
              lineHeight: message.role === "ASSISTANT" ? 1.75 : 1.6,
              color: message.role === "ASSISTANT" ? "#edf2f7" : undefined,
              paddingRight: message.role === "ASSISTANT" ? "8px" : undefined
            }}
          >
            {message.content}
          </div>
          {message.role === "ASSISTANT" ? (
            <AssistantArtifactsCard artifacts={messageArtifacts[message.messageId]} />
          ) : null}
        </article>
      ))}

      {streamingAssistantMessage ? (
        <article
          style={{
            width: "100%",
            minWidth: 0,
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
              ...textStyles.body,
              minWidth: 0,
              maxWidth: "100%",
              overflowWrap: "anywhere",
              whiteSpace: "pre-line",
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

function AssistantArtifactsCard({artifacts}: {artifacts?: AgentArtifacts}) {
  if (!artifacts) {
    return null;
  }

  const error = asText(artifacts.error);
  if (error) {
    return (
      <div
        style={{
          minWidth: 0,
          maxWidth: "100%",
          overflow: "hidden",
          borderRadius: "14px",
          border: "1px solid rgba(255,130,130,0.28)",
          background: "rgba(42,23,23,0.82)",
          padding: "12px 14px",
          display: "grid",
          gap: "8px"
        }}
      >
        <div style={{...textStyles.bodySmallStrong, color: "#ffd4d4"}}>Workflow Failed</div>
        <ArtifactRow label="Reason" value={error} mono tone="danger" />
      </div>
    );
  }

  const workflow = asText(artifacts.workflow);
  const requiresConfirmation = artifacts.requiresConfirmation === true;
  if (requiresConfirmation) {
    return null;
  }

  if (workflow === "ANALYZE_REFERENCE") {
    const styleId = asText(artifacts.styleId);
    const outputDir = asText(artifacts.outputDir);
    const elasticTemplatePath = asText(artifacts.elasticTemplatePath);

    if (!outputDir && !elasticTemplatePath) {
      return null;
    }

    return (
      <ArtifactPanel
        eyebrow="AI4VIDEO"
        title="参考视频分析完成"
        description="风格经验已经沉淀，可以继续用它来剪 source 素材。"
      >
        <ArtifactStatGrid
          items={[
            {label: "Style", value: styleId ?? "unknown"}
          ]}
        />
      </ArtifactPanel>
    );
  }

  if (workflow === "CREATE_STYLED_VIDEO") {
    const renderOutputPath = asText(artifacts.renderOutputPath);
    const plannerProvider = asText(artifacts.plannerProvider);
    const selectedVideoClipCount = asNumber(artifacts.selectedVideoClipCount);
    const targetDurationMs = asNumber(artifacts.targetDurationMs);

    return (
      <ArtifactPanel
        eyebrow="NATIVE RENDER"
        title="Demo 成片已生成"
        description="模型已根据参考经验完成选片、时间线规划和本地渲染。"
      >
        <ArtifactStatGrid
          items={[
            ...(selectedVideoClipCount ? [{label: "Clips", value: `${selectedVideoClipCount}`}] : []),
            ...(targetDurationMs ? [{label: "Duration", value: `${Math.round(targetDurationMs / 1000)}s`}] : []),
            ...(plannerProvider ? [{label: "Planner", value: plannerProvider}] : [])
          ]}
        />
        {renderOutputPath ? <ArtifactPath label="成片视频" value={renderOutputPath} accent /> : null}
      </ArtifactPanel>
    );
  }

  return null;
}

function ArtifactPanel({
  eyebrow,
  title,
  description,
  children
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <div
      style={{
        minWidth: 0,
        maxWidth: "min(100%, 620px)",
        overflow: "hidden",
        borderRadius: "18px",
        border: "1px solid rgba(121,192,255,0.24)",
        background:
          "linear-gradient(145deg, rgba(17,24,32,0.96), rgba(12,18,24,0.92) 58%, rgba(34,52,54,0.78))",
        boxShadow: "0 18px 44px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.05)",
        padding: "14px",
        display: "grid",
        gap: "12px"
      }}
    >
      <div style={{display: "grid", gap: "4px"}}>
        <div style={{...textStyles.sectionLabel, color: "#89bdf0", letterSpacing: "0.12em"}}>
          {eyebrow}
        </div>
        <div style={{...textStyles.titleSmall, color: "#eef7ff"}}>{title}</div>
        <div style={{...textStyles.bodySmall, color: "#93a6b8", lineHeight: 1.55}}>
          {description}
        </div>
      </div>
      {children}
    </div>
  );
}

function ArtifactStatGrid({items}: {items: Array<{label: string; value: string}>}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(118px, 1fr))",
        gap: "8px"
      }}
    >
      {items.map((item) => (
        <div
          key={`${item.label}-${item.value}`}
          style={{
            minWidth: 0,
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.07)",
            background: "rgba(255,255,255,0.035)",
            padding: "9px 10px",
            display: "grid",
            gap: "3px"
          }}
        >
          <div style={{...textStyles.sectionLabel, color: "#6f8294"}}>{item.label}</div>
          <div
            style={{
              ...textStyles.bodySmallStrong,
              color: "#edf6ff",
              minWidth: 0,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap"
            }}
            title={item.value}
          >
            {item.value}
          </div>
        </div>
      ))}
    </div>
  );
}

function ArtifactPath({
  label,
  value,
  accent = false
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div
      style={{
        minWidth: 0,
        borderRadius: "13px",
        border: accent ? "1px solid rgba(139,222,177,0.28)" : "1px solid rgba(255,255,255,0.07)",
        background: accent ? "rgba(70,132,94,0.16)" : "rgba(4,9,14,0.45)",
        padding: "10px 11px",
        display: "grid",
        gap: "5px"
      }}
    >
      <div style={{...textStyles.sectionLabel, color: accent ? "#9be5b6" : "#7f95aa"}}>
        {label}
      </div>
      <div
        style={{
          ...textStyles.bodySmall,
          fontFamily: fontFamilyMono,
          fontSize: "11px",
          color: accent ? "#d7ffe3" : "#c7e2ff",
          minWidth: 0,
          maxWidth: "100%",
          overflowWrap: "anywhere",
          wordBreak: "break-all",
          lineHeight: 1.55
        }}
      >
        {value}
      </div>
    </div>
  );
}

function ArtifactRow({
  label,
  value,
  mono = false,
  tone = "default"
}: {
  label: string;
  value: string;
  mono?: boolean;
  tone?: "default" | "danger";
}) {
  return (
    <div style={{display: "grid", gap: "2px", minWidth: 0, maxWidth: "100%"}}>
      <div style={{...textStyles.sectionLabel, color: "#7f95aa"}}>{label}</div>
      <div
        style={{
          ...(mono
            ? {
                ...textStyles.bodySmall,
                fontFamily: fontFamilyMono,
                fontSize: "11px"
              }
            : textStyles.bodySmall),
          color: tone === "danger" ? "#ffd4d4" : mono ? "#c7e2ff" : "#e7edf4",
          minWidth: 0,
          maxWidth: "100%",
          overflowWrap: "anywhere",
          wordBreak: mono ? "break-all" : "normal"
        }}
      >
        {value}
      </div>
    </div>
  );
}

function asText(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function asNumber(value: unknown) {
  return typeof value === "number" ? value : null;
}
