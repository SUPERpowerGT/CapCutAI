"use client";

import {AssetsSidebar} from "../../assets/components/AssetsSidebar";
import {EditorSurface} from "../../editor/components/EditorSurface";
import {ChatPanel} from "../../im/components/ChatPanel";
import {useImWorkspace} from "../../im/hooks/use-im-workspace";
import {useWorkspaceLayout} from "../hooks/use-workspace-layout";

const appShellStyle = {
  minHeight: "100vh",
  height: "100vh",
  padding: "12px",
  background: "#0f1113"
};

const frameStyle = {
  height: "calc(100vh - 24px)",
  display: "grid",
  gridTemplateRows: "44px 1fr",
  borderRadius: "20px",
  overflow: "hidden",
  border: "1px solid rgba(255,255,255,0.08)",
  background: "#15181b",
  boxShadow: "0 24px 64px rgba(0,0,0,0.35)"
};

export function WorkspaceShell() {
  const layout = useWorkspaceLayout();
  const imWorkspace = useImWorkspace();

  return (
    <main style={appShellStyle}>
      <section style={frameStyle}>
        <header
          style={{
            display: "flex",
            alignItems: "center",
            padding: "0 16px",
            background: "linear-gradient(180deg, #1b1f23 0%, #171a1d 100%)",
            borderBottom: "1px solid rgba(255,255,255,0.06)"
          }}
        >
          <div style={{fontSize: "13px", fontWeight: 600, color: "#e9edf0"}}>CapCutAI</div>
        </header>

        <div
          ref={layout.containerRef}
          style={{
            minHeight: 0,
            display: "grid",
            gridTemplateColumns: `${layout.leftPaneWidth}% 8px minmax(0, 1fr) 8px ${layout.rightPaneWidth}%`
          }}
        >
          <AssetsSidebar />

          <ResizeHandle direction="vertical" onMouseDown={layout.startLeftResize} />

          <EditorSurface
            title={imWorkspace.activeConversation?.title ?? "New Conversation"}
            previewHeightPercent={layout.previewHeight}
            onResizeStart={layout.startHorizontalResize}
          />

          <ResizeHandle direction="vertical" onMouseDown={layout.startRightResize} />

          <ChatPanel
            messages={imWorkspace.messages}
            agentStatus={imWorkspace.agentStatus}
            taskSummary={imWorkspace.taskSummary}
            currentActivity={imWorkspace.currentActivity}
            prompt={imWorkspace.prompt}
            error={imWorkspace.error}
            isBooting={imWorkspace.isBooting}
            isLoadingMessages={imWorkspace.isLoadingMessages}
            isSending={imWorkspace.isSending}
            isStreamingAssistant={imWorkspace.isStreamingAssistant}
            streamingAssistantMessage={imWorkspace.streamingAssistantMessage}
            messageEndRef={imWorkspace.messageEndRef}
            onPromptChange={imWorkspace.setPrompt}
            onSend={() => void imWorkspace.sendMessageAction()}
            onCreateConversation={() => void imWorkspace.createConversationAction()}
          />
        </div>
      </section>
    </main>
  );
}

function ResizeHandle({
  direction,
  onMouseDown
}: {
  direction: "vertical";
  onMouseDown: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={`Resize ${direction} pane`}
      onMouseDown={onMouseDown}
      style={{
        appearance: "none",
        border: 0,
        padding: 0,
        margin: 0,
        cursor: "col-resize",
        background: "transparent",
        position: "relative"
      }}
    >
      <span
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: "50%",
          width: "1px",
          background: "rgba(255,255,255,0.12)",
          transform: "translateX(-50%)"
        }}
      />
    </button>
  );
}
