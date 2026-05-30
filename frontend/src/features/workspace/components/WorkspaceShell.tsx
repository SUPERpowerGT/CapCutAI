"use client";

import {AssetsSidebar} from "../../assets/components/AssetsSidebar";
import {useAssetsPanel} from "../../assets/hooks/use-assets-panel";
import {EditorSurface} from "../../editor/components/EditorSurface";
import {ChatPanel} from "../../im/components/ChatPanel";
import {useImWorkspace} from "../../im/hooks/use-im-workspace";
import {useWorkspaceContext} from "../hooks/use-workspace-context";
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
  const workspace = useWorkspaceContext();
  const assetsPanel = useAssetsPanel();
  const imWorkspace = useImWorkspace(workspace.workspaceContext.workspaceId);

  return (
    <main style={appShellStyle}>
      <section style={frameStyle}>
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "16px",
            padding: "0 16px",
            background: "linear-gradient(180deg, #1b1f23 0%, #171a1d 100%)",
            borderBottom: "1px solid rgba(255,255,255,0.06)"
          }}
        >
          <div style={{display: "grid", gap: "2px"}}>
            <div style={{fontSize: "13px", fontWeight: 600, color: "#e9edf0"}}>CapCutAI</div>
            <div style={{fontSize: "11px", color: "#8d96a0"}}>{workspace.workspaceContext.title}</div>
          </div>
          <div
            style={{
              fontSize: "11px",
              color: "#7d8792",
              letterSpacing: "0.08em",
              textTransform: "uppercase"
            }}
          >
            Desktop Workspace
          </div>
        </header>

        <div
          ref={layout.containerRef}
          style={{
            minHeight: 0,
            display: "grid",
            gridTemplateColumns: `${layout.leftPaneWidth}% 8px minmax(0, 1fr) 8px ${layout.rightPaneWidth}%`
          }}
        >
          <AssetsSidebar
            workspaceTitle={workspace.workspaceContext.title}
            referenceAssets={assetsPanel.referenceAssets}
            sourceAssets={assetsPanel.sourceAssets}
            selectedReferenceAssetId={assetsPanel.selectedReferenceAssetId}
            selectedSourceAssetId={assetsPanel.selectedSourceAssetId}
            isPicking={assetsPanel.isPicking}
            isRegistering={assetsPanel.isRegistering}
            error={assetsPanel.error}
            onAddReferenceVideo={assetsPanel.addReferenceVideo}
            onAddSourceVideo={assetsPanel.addSourceVideo}
            onRemoveAsset={assetsPanel.removeAsset}
            onSelectReferenceAsset={assetsPanel.selectReferenceAsset}
            onSelectSourceAsset={assetsPanel.selectSourceAsset}
          />

          <ResizeHandle direction="vertical" onMouseDown={layout.startLeftResize} />

          <EditorSurface
            title={workspace.workspaceContext.title}
            subtitle={
              assetsPanel.selectedReferenceAsset || assetsPanel.selectedSourceAsset
                ? [
                    assetsPanel.selectedReferenceAsset ? "Reference ready" : "Reference missing",
                    assetsPanel.selectedSourceAsset ? "Source ready" : "Source missing"
                  ].join(" · ")
                : "Select reference and source assets to start the workflow"
            }
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
