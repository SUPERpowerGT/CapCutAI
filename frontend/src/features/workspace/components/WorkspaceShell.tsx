"use client";

import {useEffect, useRef, useState} from "react";
import type {MouseEvent as ReactMouseEvent, ReactNode} from "react";
import {AssetsSidebar} from "../../assets/components/AssetsSidebar";
import type {AssetItem} from "../../assets/types/assets";
import {useAssetsPanel} from "../../assets/hooks/use-assets-panel";
import {EditorSurface} from "../../editor/components/EditorSurface";
import {ChatPanel} from "../../im/components/ChatPanel";
import {useImWorkspace} from "../../im/hooks/use-im-workspace";
import type {AgentWorkspaceContext} from "../../im/types/contracts";
import {textStyles} from "../../../shared/design/typography";
import {useWorkspaceContext} from "../hooks/use-workspace-context";
import {useWorkspaceLayout} from "../hooks/use-workspace-layout";

const appShellStyle = {
  minHeight: "100dvh",
  height: "100dvh",
  background: "#0f1113"
};

const frameStyle = {
  height: "100%",
  display: "grid",
  gridTemplateRows: "44px 1fr",
  overflow: "hidden",
  background: "#15181b"
};

export function WorkspaceShell() {
  const layout = useWorkspaceLayout();
  const workspace = useWorkspaceContext();
  const assetsPanel = useAssetsPanel(
    workspace.isReady ? workspace.workspaceContext.workspaceId : null
  );
  const workspaceFolderPath = workspace.isReady
    ? workspace.workspaceContext.folderPath
    : undefined;
  const referenceDirectoryPath = workspaceFolderPath
    ? `${workspaceFolderPath}/assets/reference/current`
    : undefined;
  const sourceDirectoryPath = workspaceFolderPath
    ? `${workspaceFolderPath}/assets/source`
    : undefined;
  const agentWorkspaceContext: AgentWorkspaceContext = {
    workspaceId: workspace.isReady ? workspace.workspaceContext.workspaceId : undefined,
    workspaceTitle: workspace.workspaceContext.title,
    workspaceFolderPath,
    referenceDirectoryPath,
    sourceDirectoryPath,
    hasReferenceVideo: Boolean(assetsPanel.selectedReferenceAsset),
    hasSourceVideo: assetsPanel.sourceAssets.length > 0,
    referenceVideo: assetsPanel.selectedReferenceAsset
      ? {
          assetId: assetsPanel.selectedReferenceAsset.assetId,
          name: assetsPanel.selectedReferenceAsset.name,
          mimeType: assetsPanel.selectedReferenceAsset.mimeType,
          durationSeconds: assetsPanel.selectedReferenceAsset.durationSeconds,
          frameWidth: assetsPanel.selectedReferenceAsset.frameWidth,
          frameHeight: assetsPanel.selectedReferenceAsset.frameHeight,
          workspaceFilePath: assetsPanel.selectedReferenceAsset.workspaceFilePath,
          workspaceRelativePath:
            assetsPanel.selectedReferenceAsset.workspaceRelativePath
        }
      : null,
    sourceVideo: assetsPanel.selectedSourceAsset
      ? {
          assetId: assetsPanel.selectedSourceAsset.assetId,
          name: assetsPanel.selectedSourceAsset.name,
          mimeType: assetsPanel.selectedSourceAsset.mimeType,
          durationSeconds: assetsPanel.selectedSourceAsset.durationSeconds,
          frameWidth: assetsPanel.selectedSourceAsset.frameWidth,
          frameHeight: assetsPanel.selectedSourceAsset.frameHeight,
          workspaceFilePath: assetsPanel.selectedSourceAsset.workspaceFilePath,
          workspaceRelativePath: assetsPanel.selectedSourceAsset.workspaceRelativePath
        }
      : null,
    sourceVideos: assetsPanel.sourceAssets.map((asset) => ({
      assetId: asset.assetId,
      name: asset.name,
      mimeType: asset.mimeType,
      durationSeconds: asset.durationSeconds,
      frameWidth: asset.frameWidth,
      frameHeight: asset.frameHeight,
      workspaceFilePath: asset.workspaceFilePath,
      workspaceRelativePath: asset.workspaceRelativePath
    }))
  };
  const imWorkspace = useImWorkspace(
    workspace.isReady ? workspace.workspaceContext.workspaceId : null,
    agentWorkspaceContext
  );
  const timelineDropZoneRef = useRef<HTMLDivElement | null>(null);
  const [dragCandidate, setDragCandidate] = useState<{
    asset: AssetItem;
    startX: number;
    startY: number;
    currentX: number;
    currentY: number;
  } | null>(null);
  const [activeTimelineDrag, setActiveTimelineDrag] = useState<{
    asset: AssetItem;
    x: number;
    y: number;
  } | null>(null);
  const [externalTimelineDropRequest, setExternalTimelineDropRequest] = useState<{
    assetId: string;
    clientX: number;
    clientY: number;
    nonce: number;
  } | null>(null);

  useEffect(() => {
    if (!dragCandidate) {
      return;
    }
    const candidate = dragCandidate;

    function handleMouseMove(event: MouseEvent) {
      const nextX = event.clientX;
      const nextY = event.clientY;
      const distance = Math.hypot(nextX - candidate.startX, nextY - candidate.startY);

      if (distance > 6) {
        setActiveTimelineDrag({
          asset: candidate.asset,
          x: nextX,
          y: nextY
        });
      }

      setDragCandidate((current) =>
        current
          ? {
              ...current,
              currentX: nextX,
              currentY: nextY
            }
          : current
      );
    }

    function handleMouseUp(event: MouseEvent) {
      const dropZone = timelineDropZoneRef.current;
      if (dropZone && activeTimelineDrag) {
        const rect = dropZone.getBoundingClientRect();
        const insideDropZone =
          event.clientX >= rect.left &&
          event.clientX <= rect.right &&
          event.clientY >= rect.top &&
          event.clientY <= rect.bottom;

        if (insideDropZone) {
          setExternalTimelineDropRequest({
            assetId: activeTimelineDrag.asset.assetId,
            clientX: event.clientX,
            clientY: event.clientY,
            nonce: Date.now()
          });
        }
      }

      setDragCandidate(null);
      setActiveTimelineDrag(null);
    }

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [activeTimelineDrag, dragCandidate]);

  function handleStartSourceTimelineDrag(asset: AssetItem, event: ReactMouseEvent<HTMLDivElement>) {
    setDragCandidate({
      asset,
      startX: event.clientX,
      startY: event.clientY,
      currentX: event.clientX,
      currentY: event.clientY
    });
  }

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
          <div style={textStyles.windowTitle}>CapCutAI</div>
          <div style={{display: "flex", alignItems: "center", gap: "8px"}}>
            <WindowToggleButton
              label="Toggle Assets"
              active={!layout.isLeftPaneCollapsed}
              onClick={layout.toggleLeftPane}
              icon={<PanelIcon side="left" />}
            />
            <WindowToggleButton
              label="Toggle Timeline"
              active={!layout.isBottomPaneCollapsed}
              onClick={layout.toggleBottomPane}
              icon={<PanelIcon side="bottom" />}
            />
            <WindowToggleButton
              label="Toggle Agent"
              active={!layout.isRightPaneCollapsed}
              onClick={layout.toggleRightPane}
              icon={<PanelIcon side="right" />}
            />
          </div>
        </header>

        <div
          ref={layout.containerRef}
          style={{
            minHeight: 0,
            display: "grid",
            gridTemplateColumns: `${layout.isLeftPaneCollapsed ? 0 : layout.leftPaneWidth}% ${
              layout.isLeftPaneCollapsed ? 0 : 8
            }px minmax(0, 1fr) ${layout.isRightPaneCollapsed ? 0 : 8}px ${
              layout.isRightPaneCollapsed ? 0 : layout.rightPaneWidth
            }%`
          }}
        >
          {!layout.isLeftPaneCollapsed ? (
            <AssetsSidebar
              workspaceTitle={workspace.workspaceContext.title}
              referenceAssets={assetsPanel.referenceAssets}
              selectedReferenceAssetId={assetsPanel.selectedReferenceAssetId}
              selectedPreviewAssetId={assetsPanel.selectedPreviewAssetId}
              sourceAssets={assetsPanel.sourceAssets}
              selectedSourceAssetId={assetsPanel.selectedSourceAssetId}
              isPicking={assetsPanel.isPicking}
              isRegistering={assetsPanel.isRegistering}
              error={assetsPanel.error}
              onAddReferenceVideo={assetsPanel.addReferenceVideo}
              onAddSourceVideo={assetsPanel.addSourceVideo}
              onRemoveAsset={assetsPanel.removeAsset}
              onSelectReferenceAsset={assetsPanel.selectReferenceAsset}
              onSelectSourceAsset={assetsPanel.selectSourceAsset}
              onStartSourceTimelineDrag={handleStartSourceTimelineDrag}
            />
          ) : (
            <div />
          )}

          {!layout.isLeftPaneCollapsed ? (
            <ResizeHandle direction="vertical" onMouseDown={layout.startLeftResize} />
          ) : (
            <div />
          )}

          <EditorSurface
            title={workspace.workspaceContext.title}
            subtitle={
              assetsPanel.selectedPreviewAsset
                ? "当前已加载本地视频，可以继续分析、生成或修订。"
                : "先在左侧上传一个视频，预览区会立即显示本地画面。"
            }
            workspaceId={workspace.workspaceContext.workspaceId}
            sourceAssets={assetsPanel.sourceAssets}
            selectedSourceAsset={assetsPanel.selectedSourceAsset}
            selectedPreviewAsset={assetsPanel.selectedPreviewAsset}
            previewSource={
              assetsPanel.selectedPreviewAsset
                ? {
                    objectUrl: assetsPanel.selectedPreviewAsset.objectUrl,
                    name: assetsPanel.selectedPreviewAsset.name,
                    mimeType: assetsPanel.selectedPreviewAsset.mimeType
                  }
                : null
            }
            previewHeightPercent={layout.previewHeight}
            isBottomPaneCollapsed={layout.isBottomPaneCollapsed}
            onResizeStart={layout.startHorizontalResize}
            externalTimelineDropRequest={externalTimelineDropRequest}
            externalTimelineDrag={
              activeTimelineDrag
                ? {
                    assetId: activeTimelineDrag.asset.assetId,
                    label: activeTimelineDrag.asset.name,
                    clientX: activeTimelineDrag.x,
                    clientY: activeTimelineDrag.y
                  }
                : null
            }
            onTimelineDropZoneElementChange={(element) => {
              timelineDropZoneRef.current = element;
            }}
          />

          {!layout.isRightPaneCollapsed ? (
            <ResizeHandle direction="vertical" onMouseDown={layout.startRightResize} />
          ) : (
            <div />
          )}

          {!layout.isRightPaneCollapsed ? (
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
          ) : (
            <div />
          )}
        </div>
      </section>
      {activeTimelineDrag ? (
        <div
          style={{
            position: "fixed",
            left: `${activeTimelineDrag.x + 12}px`,
            top: `${activeTimelineDrag.y + 12}px`,
            padding: "10px 12px",
            borderRadius: "10px",
            background: "rgba(33,40,48,0.96)",
            border: "1px solid rgba(121,192,255,0.24)",
            boxShadow: "0 16px 36px rgba(0,0,0,0.28)",
            pointerEvents: "none",
            zIndex: 1000,
            maxWidth: "240px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            ...textStyles.bodySmallStrong,
            color: "#e7f2ff"
          }}
        >
          {activeTimelineDrag.asset.name}
        </div>
      ) : null}
    </main>
  );
}

function WindowToggleButton({
  label,
  active,
  icon,
  onClick
}: {
  label: string;
  active: boolean;
  icon: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      style={{
        appearance: "none",
        width: "28px",
        height: "28px",
        borderRadius: "8px",
        border: active ? "1px solid rgba(255,255,255,0.12)" : "1px solid transparent",
        background: active ? "#23282d" : "transparent",
        color: active ? "#e7edf2" : "#8d96a0",
        display: "grid",
        placeItems: "center",
        padding: 0,
        ...textStyles.iconButton,
        cursor: "pointer"
      }}
    >
      {icon}
    </button>
  );
}

function PanelIcon({side}: {side: "left" | "right" | "bottom"}) {
  return (
    <span
      style={{
        width: "14px",
        height: "14px",
        display: "grid",
        gridTemplateColumns: side === "bottom" ? "1fr" : side === "left" ? "4px 1fr" : "1fr 4px",
        gridTemplateRows: side === "bottom" ? "1fr 4px" : "1fr",
        gap: "2px"
      }}
    >
      {side === "bottom" ? (
        <>
          <span style={{background: "currentColor", borderRadius: "2px"}} />
          <span style={{background: "currentColor", opacity: 0.7, borderRadius: "2px"}} />
        </>
      ) : (
        <>
          <span style={{background: "currentColor", opacity: side === "left" ? 0.95 : 0.6, borderRadius: "2px"}} />
          <span style={{background: "currentColor", opacity: side === "right" ? 0.95 : 0.6, borderRadius: "2px"}} />
        </>
      )}
    </span>
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
