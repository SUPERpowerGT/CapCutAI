"use client";

import {useEffect, useMemo, useState} from "react";
import type {AssetItem} from "../../assets/types/assets";
import {loadMockEditingExperience} from "../data/mock-editing-experience";
import {selectMockSourceMaterials} from "../data/mock-source-material";
import {
  buildEditorExportPackage,
  downloadEditorExportPackage
} from "../lib/build-editor-export-package";
import type {EditorExportPackage, WorkspaceTimelineClip} from "../types/editor-preview";
import {PreviewViewport} from "./PreviewViewport";
import {TimelinePanel} from "./TimelinePanel";

type EditorSurfaceProps = {
  title: string;
  subtitle?: string;
  workspaceId: string;
  sourceAssets: AssetItem[];
  selectedSourceAsset: AssetItem | null;
  selectedPreviewAsset: AssetItem | null;
  previewSource?: {
    objectUrl?: string;
    name: string;
    mimeType: string;
  } | null;
  previewHeightPercent: number;
  isBottomPaneCollapsed?: boolean;
  onResizeStart: () => void;
  externalTimelineDropRequest?: {
    assetId: string;
    clientX: number;
    clientY: number;
    nonce: number;
  } | null;
  externalTimelineDrag?: {
    assetId: string;
    label: string;
    clientX: number;
    clientY: number;
  } | null;
  onTimelineDropZoneElementChange: (element: HTMLDivElement | null) => void;
};

type PreviewMode = "asset" | "timeline";

export function EditorSurface({
  title,
  subtitle,
  workspaceId,
  sourceAssets,
  selectedSourceAsset,
  selectedPreviewAsset,
  previewSource,
  previewHeightPercent,
  isBottomPaneCollapsed = false,
  onResizeStart,
  externalTimelineDropRequest = null,
  externalTimelineDrag = null,
  onTimelineDropZoneElementChange
}: EditorSurfaceProps) {
  const editingExperience = useMemo(() => loadMockEditingExperience(), []);
  const sourceMaterials = useMemo(() => selectMockSourceMaterials(sourceAssets.length), [sourceAssets.length]);
  const [lastExportPackage, setLastExportPackage] = useState<EditorExportPackage | null>(null);
  const [workspaceTimelineClips, setWorkspaceTimelineClips] = useState<WorkspaceTimelineClip[]>([]);
  const [selectedTimelineClipId, setSelectedTimelineClipId] = useState<string | null>(null);
  const [timelineElapsedMs, setTimelineElapsedMs] = useState(0);
  const [isTimelinePlaybackActive, setIsTimelinePlaybackActive] = useState(false);
  const [previewMode, setPreviewMode] = useState<PreviewMode>("asset");
  const timelineDurationMs = useMemo(
    () =>
      workspaceTimelineClips.reduce(
        (maxDurationMs, clip) => Math.max(maxDurationMs, clip.timelineStartMs + clip.durationMs),
        0
      ),
    [workspaceTimelineClips]
  );

  useEffect(() => {
    setWorkspaceTimelineClips((currentClips) =>
      normalizeTimelineClips(
        currentClips.filter((clip) => sourceAssets.some((asset) => asset.assetId === clip.assetId))
      )
    );
  }, [sourceAssets]);

  useEffect(() => {
    setSelectedTimelineClipId((currentSelectedId) => {
      if (currentSelectedId && workspaceTimelineClips.some((clip) => clip.clipId === currentSelectedId)) {
        return currentSelectedId;
      }

      return workspaceTimelineClips[0]?.clipId ?? null;
    });
  }, [workspaceTimelineClips]);

  useEffect(() => {
    if (!selectedPreviewAsset) {
      return;
    }

    setPreviewMode("asset");
    setIsTimelinePlaybackActive(false);
  }, [selectedPreviewAsset?.assetId]);

  const sourceAssetMap = useMemo(
    () => new Map(sourceAssets.map((asset) => [asset.assetId, asset])),
    [sourceAssets]
  );
  const selectedTimelineClip =
    workspaceTimelineClips.find((clip) => clip.clipId === selectedTimelineClipId) ?? null;

  const draftExportPackage = useMemo(
    () =>
      buildEditorExportPackage({
        workspaceId,
        sourceAssets,
        selectedSourceAsset,
        workspaceTimelineClips,
        experience: editingExperience,
        sourceMaterials
      }),
    [editingExperience, selectedSourceAsset, sourceAssets, sourceMaterials, workspaceId, workspaceTimelineClips]
  );

  function exportEditingPackage() {
    setLastExportPackage(draftExportPackage);
    downloadEditorExportPackage(draftExportPackage);
  }

  function addAssetToTimeline(assetId: string, preferredTimelineStartMs?: number) {
    const asset = sourceAssetMap.get(assetId);
    if (!asset) {
      return;
    }

    const defaultDurationMs = Math.max(1000, Math.round((asset.durationSeconds ?? 6) * 1000));
    const appendedTimelineStartMs = workspaceTimelineClips.reduce(
      (maxEndMs, clip) => Math.max(maxEndMs, clip.timelineStartMs + clip.durationMs),
      0
    );
    const nextClip: WorkspaceTimelineClip = {
      clipId: `workspace_clip_${crypto.randomUUID()}`,
      assetId: asset.assetId,
      label: asset.name,
      timelineStartMs: Math.max(0, preferredTimelineStartMs ?? appendedTimelineStartMs),
      sourceStartMs: 0,
      durationMs: defaultDurationMs
    };

    setWorkspaceTimelineClips((currentClips) => normalizeTimelineClips([...currentClips, nextClip]));
    setSelectedTimelineClipId(nextClip.clipId);
  }

  function removeTimelineClip(clipId: string) {
    setWorkspaceTimelineClips((currentClips) => currentClips.filter((clip) => clip.clipId !== clipId));
  }

  function updateTimelineClip(
    clipId: string,
    patch: Partial<Pick<WorkspaceTimelineClip, "timelineStartMs" | "sourceStartMs" | "durationMs">>
  ) {
    setWorkspaceTimelineClips((currentClips) =>
      normalizeTimelineClips(
        currentClips.map((clip) => (clip.clipId === clipId ? {...clip, ...patch} : clip))
      )
    );
  }

  function moveTimelineClip(fromClipId: string, nextTimelineStartMs: number) {
    setWorkspaceTimelineClips((currentClips) => {
      return normalizeTimelineClips(
        currentClips.map((clip) =>
          clip.clipId === fromClipId
            ? {...clip, timelineStartMs: Math.max(0, nextTimelineStartMs)}
            : clip
        )
      );
    });
    setSelectedTimelineClipId(fromClipId);
  }

  function splitSelectedTimelineClip() {
    if (!selectedTimelineClipId) {
      return;
    }

    const clipIndex = workspaceTimelineClips.findIndex((clip) => clip.clipId === selectedTimelineClipId);
    if (clipIndex < 0) {
      return;
    }

    const clip = workspaceTimelineClips[clipIndex];
    const localOffsetMs = timelineElapsedMs - clip.timelineStartMs;
    const snappedOffsetMs = Math.round(localOffsetMs / 200) * 200;

    if (snappedOffsetMs <= 1000 || snappedOffsetMs >= clip.durationMs - 1000) {
      return;
    }

    const firstClip: WorkspaceTimelineClip = {
      ...clip,
      durationMs: snappedOffsetMs
    };
    const secondClip: WorkspaceTimelineClip = {
      ...clip,
      clipId: `workspace_clip_${crypto.randomUUID()}`,
      timelineStartMs: clip.timelineStartMs + snappedOffsetMs,
      sourceStartMs: clip.sourceStartMs + snappedOffsetMs,
      durationMs: clip.durationMs - snappedOffsetMs
    };

    setWorkspaceTimelineClips((currentClips) =>
      normalizeTimelineClips([
        ...currentClips.slice(0, clipIndex),
        firstClip,
        secondClip,
        ...currentClips.slice(clipIndex + 1)
      ])
    );
    setSelectedTimelineClipId(secondClip.clipId);
  }

  function seekTimeline(nextElapsedMs: number) {
    const safeElapsedMs = Math.max(0, Math.min(nextElapsedMs, timelineDurationMs));
    setTimelineElapsedMs(safeElapsedMs);

    for (const clip of workspaceTimelineClips) {
      const clipEndMs = clip.timelineStartMs + clip.durationMs;
      if (safeElapsedMs >= clip.timelineStartMs && safeElapsedMs < clipEndMs) {
        setSelectedTimelineClipId(clip.clipId);
        return;
      }
    }

    const nextClip = workspaceTimelineClips.find((clip) => clip.timelineStartMs >= safeElapsedMs);
    if (nextClip) {
      setSelectedTimelineClipId(nextClip.clipId);
      return;
    }

    setSelectedTimelineClipId(workspaceTimelineClips[workspaceTimelineClips.length - 1]?.clipId ?? null);
  }

  function handleTimelineSeek(nextElapsedMs: number) {
    setPreviewMode("timeline");
    seekTimeline(nextElapsedMs);
  }

  function toggleTimelinePlayback() {
    if (!workspaceTimelineClips.length) {
      return;
    }

    setPreviewMode("timeline");
    if (!selectedTimelineClipId) {
      seekTimeline(0);
    }

    setIsTimelinePlaybackActive((current) => !current);
  }

  return (
    <section
      style={{
        minHeight: 0,
        display: "grid",
        gridTemplateRows: isBottomPaneCollapsed
          ? "minmax(0, 1fr)"
          : `minmax(220px, ${previewHeightPercent}%) 8px minmax(180px, ${100 - previewHeightPercent}%)`,
        background: "#121518"
      }}
    >
      <PreviewViewport
        title={title}
        subtitle={subtitle}
        previewSource={previewSource}
        selectedPreviewAsset={selectedPreviewAsset}
        selectedSourceAsset={selectedSourceAsset}
        previewMode={previewMode}
        timelineAssets={sourceAssets}
        timelineClips={workspaceTimelineClips}
        selectedTimelineClipId={selectedTimelineClipId}
        timelineElapsedMs={timelineElapsedMs}
        isTimelinePlaybackActive={isTimelinePlaybackActive}
        onTimelineElapsedMsChange={setTimelineElapsedMs}
        onTimelinePlaybackActiveChange={setIsTimelinePlaybackActive}
        onActiveTimelineClipChange={setSelectedTimelineClipId}
        onRequestTimelinePreview={() => setPreviewMode("timeline")}
        sourceAssetCount={sourceAssets.length}
        editingExperience={editingExperience}
        sourceMaterials={sourceMaterials}
      />
      {!isBottomPaneCollapsed ? (
        <>
          <button
            type="button"
            aria-label="Resize preview and timeline"
            onMouseDown={onResizeStart}
            style={{
              appearance: "none",
              border: 0,
              padding: 0,
              margin: 0,
              cursor: "row-resize",
              background: "transparent",
              position: "relative"
            }}
          >
            <span
              style={{
                position: "absolute",
                top: "50%",
                left: 0,
                right: 0,
                height: "1px",
                background: "rgba(255,255,255,0.12)",
                transform: "translateY(-50%)"
              }}
            />
          </button>
          <TimelinePanel
            sourceAssets={sourceAssets}
            editingExperience={editingExperience}
            sourceMaterials={sourceMaterials}
            timelinePlan={draftExportPackage.timelinePlan}
            editingJob={draftExportPackage.editingJob}
            timelineClips={workspaceTimelineClips}
            externalTimelineDrag={externalTimelineDrag}
            externalTimelineDropRequest={externalTimelineDropRequest}
            selectedTimelineClipId={selectedTimelineClipId}
            timelineElapsedMs={timelineElapsedMs}
            isTimelinePlaybackActive={isTimelinePlaybackActive}
            onSelectTimelineClip={setSelectedTimelineClipId}
            onSeekTimeline={handleTimelineSeek}
            onToggleTimelinePlayback={toggleTimelinePlayback}
            onAddAssetToTimeline={addAssetToTimeline}
            onMoveTimelineClip={moveTimelineClip}
            onUpdateTimelineClip={updateTimelineClip}
            onRemoveTimelineClip={removeTimelineClip}
            onSplitTimelineClip={splitSelectedTimelineClip}
            lastExportPackage={lastExportPackage}
            onExportEditingPackage={exportEditingPackage}
            onTimelineDropZoneElementChange={onTimelineDropZoneElementChange}
          />
        </>
      ) : null}
    </section>
  );
}

function normalizeTimelineClips(clips: WorkspaceTimelineClip[]) {
  const sortedClips = [...clips].sort((left, right) => {
    if (left.timelineStartMs !== right.timelineStartMs) {
      return left.timelineStartMs - right.timelineStartMs;
    }

    return left.clipId.localeCompare(right.clipId);
  });

  let previousClipEndMs = 0;
  return sortedClips.map((clip) => {
    const normalizedClip = {
      ...clip,
      timelineStartMs: Math.max(previousClipEndMs, clip.timelineStartMs)
    };
    previousClipEndMs = normalizedClip.timelineStartMs + normalizedClip.durationMs;
    return normalizedClip;
  });
}
