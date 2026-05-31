import {useEffect, useMemo, useRef, useState} from "react";
import {textStyles} from "../../../shared/design/typography";
import type {AssetItem} from "../../assets/types/assets";
import type {
  EditingExperience,
  EditingJob,
  EditorExportPackage,
  SourceMaterial,
  TimelinePlan,
  WorkspaceTimelineClip
} from "../types/editor-preview";

type TimelinePanelProps = {
  sourceAssets: AssetItem[];
  editingExperience: EditingExperience;
  sourceMaterials: SourceMaterial[];
  timelinePlan: TimelinePlan;
  editingJob: EditingJob;
  timelineClips: WorkspaceTimelineClip[];
  externalTimelineDrag?: {
    assetId: string;
    label: string;
    clientX: number;
    clientY: number;
  } | null;
  externalTimelineDropRequest?: {
    assetId: string;
    clientX: number;
    clientY: number;
    nonce: number;
  } | null;
  selectedTimelineClipId: string | null;
  timelineElapsedMs: number;
  isTimelinePlaybackActive: boolean;
  onSelectTimelineClip: (clipId: string | null) => void;
  onSeekTimeline: (elapsedMs: number) => void;
  onToggleTimelinePlayback: () => void;
  onAddAssetToTimeline: (assetId: string, preferredTimelineStartMs?: number) => void;
  onMoveTimelineClip: (clipId: string, nextTimelineStartMs: number) => void;
  onUpdateTimelineClip: (
    clipId: string,
    patch: Partial<Pick<WorkspaceTimelineClip, "timelineStartMs" | "sourceStartMs" | "durationMs">>
  ) => void;
  onRemoveTimelineClip: (clipId: string) => void;
  onSplitTimelineClip: () => void;
  lastExportPackage: EditorExportPackage | null;
  onExportEditingPackage: () => void;
  onTimelineDropZoneElementChange: (element: HTMLDivElement | null) => void;
};

const sectionLabelStyle = textStyles.sectionLabel;
const laneHeight = 44;
const snapStepMs = 200;
const zoomPresets = [
  {pixelsPerSecond: 240, majorTickSeconds: 1},
  {pixelsPerSecond: 180, majorTickSeconds: 5},
  {pixelsPerSecond: 120, majorTickSeconds: 10},
  {pixelsPerSecond: 64, majorTickSeconds: 30},
  {pixelsPerSecond: 36, majorTickSeconds: 60}
] as const;

export function TimelinePanel({
  sourceAssets,
  timelineClips,
  externalTimelineDrag = null,
  externalTimelineDropRequest = null,
  selectedTimelineClipId,
  timelineElapsedMs,
  isTimelinePlaybackActive,
  onSelectTimelineClip,
  onSeekTimeline,
  onToggleTimelinePlayback,
  onAddAssetToTimeline,
  onMoveTimelineClip,
  onUpdateTimelineClip,
  onRemoveTimelineClip,
  onSplitTimelineClip,
  onExportEditingPackage,
  onTimelineDropZoneElementChange
}: TimelinePanelProps) {
  const timelineScrollRef = useRef<HTMLDivElement | null>(null);
  const [draggingTimelineClipId, setDraggingTimelineClipId] = useState<string | null>(null);
  const [zoomPresetIndex, setZoomPresetIndex] = useState(3);
  const [laneControls, setLaneControls] = useState<Record<string, {locked: boolean; muted: boolean; visible: boolean}>>({
    "video-main": {locked: false, muted: false, visible: true},
    "video-cutaway": {locked: false, muted: false, visible: true},
    "video-overlay": {locked: false, muted: false, visible: true},
    subtitle: {locked: false, muted: false, visible: true},
    "subtitle-secondary": {locked: false, muted: false, visible: true},
    "audio-main": {locked: false, muted: false, visible: true},
    "audio-secondary": {locked: false, muted: false, visible: true},
    "audio-ambience": {locked: false, muted: false, visible: true}
  });
  const [playheadDragStartX, setPlayheadDragStartX] = useState<number | null>(null);
  const [clipDragSession, setClipDragSession] = useState<{
    clipId: string;
    startX: number;
    initialTimelineStartMs: number;
  } | null>(null);
  const [trimSession, setTrimSession] = useState<{
    clipId: string;
    edge: "start" | "end";
    startX: number;
    initialSourceStartMs: number;
    initialDurationMs: number;
    assetDurationMs: number;
  } | null>(null);
  const lastHandledExternalDropNonceRef = useRef<number | null>(null);
  const assetMap = useMemo(
    () => new Map(sourceAssets.map((asset) => [asset.assetId, asset])),
    [sourceAssets]
  );
  const activeZoomPreset = zoomPresets[zoomPresetIndex] ?? zoomPresets[3];
  const pixelsPerSecond = activeZoomPreset.pixelsPerSecond;
  const timelineDurationMs = timelineClips.reduce(
    (maxDurationMs, clip) => Math.max(maxDurationMs, clip.timelineStartMs + clip.durationMs),
    0
  );
  const workspaceDurationMs = Math.max(10 * 60 * 1000, timelineDurationMs + 2 * 60 * 1000);
  const workspaceWidth = Math.max(960, Math.round((workspaceDurationMs / 1000) * pixelsPerSecond));
  const selectedTimelineClip =
    timelineClips.find((clip) => clip.clipId === selectedTimelineClipId) ?? null;
  const selectedTimelineAsset = selectedTimelineClip
    ? assetMap.get(selectedTimelineClip.assetId) ?? null
    : null;
  const lanes = [
    {id: "video-main", label: "V1", acceptsClips: true},
    {id: "video-cutaway", label: "V2", acceptsClips: false},
    {id: "video-overlay", label: "V3", acceptsClips: false},
    {id: "subtitle", label: "T1", acceptsClips: false},
    {id: "subtitle-secondary", label: "T2", acceptsClips: false},
    {id: "audio-main", label: "A1", acceptsClips: false},
    {id: "audio-secondary", label: "A2", acceptsClips: false},
    {id: "audio-ambience", label: "A3", acceptsClips: false}
  ] as const;

  const clipOffsets = timelineClips.reduce<Record<string, number>>((accumulator, clip) => {
    accumulator[clip.clipId] = clip.timelineStartMs;
    return accumulator;
  }, {});
  const timelineSnapPointsMs = timelineClips.flatMap((clip) => {
    const clipStartMs = clipOffsets[clip.clipId] ?? 0;
    return [clipStartMs, clipStartMs + clip.durationMs];
  });
  const playheadLeft = Math.max(0, Math.min(workspaceWidth, Math.round((timelineElapsedMs / 1000) * pixelsPerSecond)));
  const externalDropPreview = useMemo(() => {
    if (!externalTimelineDrag || !onTimelineDropZoneElementChange) {
      return null;
    }

    return null;
  }, [externalTimelineDrag, onTimelineDropZoneElementChange]);

  function readDraggedAssetId(dataTransfer: DataTransfer) {
    return (
      dataTransfer.getData("application/x-capcutai-source-asset") ||
      dataTransfer.getData("text/plain") ||
      ""
    );
  }

  function getElapsedMsFromClientX(clientX: number) {
    const dropZone = timelineScrollRef.current?.querySelector<HTMLDivElement>("[data-timeline-dropzone='true']");
    const scrollContainer = timelineScrollRef.current;
    if (!dropZone || !scrollContainer) {
      return 0;
    }

    const rect = dropZone.getBoundingClientRect();
    const contentOffsetX = scrollContainer.scrollLeft + (clientX - rect.left);
    return snapToTimelinePoint(
      Math.round((Math.max(0, Math.min(workspaceWidth, contentOffsetX)) / pixelsPerSecond) * 1000),
      timelineSnapPointsMs
    );
  }

  const externalDropIndicatorMs = externalTimelineDrag
    ? getElapsedMsFromClientX(externalTimelineDrag.clientX)
    : null;
  const activeClipDragIndicatorMs = clipDragSession
    ? timelineClips.find((clip) => clip.clipId === clipDragSession.clipId)?.timelineStartMs ?? null
    : null;
  const insertionIndicatorMs = externalDropIndicatorMs ?? activeClipDragIndicatorMs;

  useEffect(() => {
    if (!externalTimelineDropRequest) {
      return;
    }

    if (lastHandledExternalDropNonceRef.current === externalTimelineDropRequest.nonce) {
      return;
    }

    lastHandledExternalDropNonceRef.current = externalTimelineDropRequest.nonce;
    onAddAssetToTimeline(
      externalTimelineDropRequest.assetId,
      getElapsedMsFromClientX(externalTimelineDropRequest.clientX)
    );
  }, [externalTimelineDropRequest, onAddAssetToTimeline]);

  useEffect(() => {
    if (!clipDragSession) {
      return;
    }
    const session = clipDragSession;

    function handlePointerMove(event: MouseEvent) {
      const deltaMs = snapToStep(
        Math.round(((event.clientX - session.startX) / pixelsPerSecond) * 1000),
        snapStepMs
      );
      onMoveTimelineClip(session.clipId, Math.max(0, session.initialTimelineStartMs + deltaMs));
    }

    function handlePointerUp() {
      setDraggingTimelineClipId(null);
      setClipDragSession(null);
    }

    window.addEventListener("mousemove", handlePointerMove);
    window.addEventListener("mouseup", handlePointerUp);
    return () => {
      window.removeEventListener("mousemove", handlePointerMove);
      window.removeEventListener("mouseup", handlePointerUp);
    };
  }, [clipDragSession, onMoveTimelineClip, pixelsPerSecond]);

  useEffect(() => {
    if (!trimSession) {
      return;
    }
    const session = trimSession;

    function handlePointerMove(event: MouseEvent) {
      const deltaMs = snapToStep(
        Math.round(((event.clientX - session.startX) / pixelsPerSecond) * 1000),
        snapStepMs
      );

      if (session.edge === "start") {
        const nextSourceStartMs = snapToStep(
          Math.max(
            0,
            Math.min(
              session.initialSourceStartMs + deltaMs,
              session.assetDurationMs - 1000
            )
          ),
          snapStepMs
        );
        const consumedDeltaMs = nextSourceStartMs - session.initialSourceStartMs;
        const nextDurationMs = snapToStep(
          Math.max(1000, session.initialDurationMs - consumedDeltaMs),
          snapStepMs
        );
        onUpdateTimelineClip(session.clipId, {
          sourceStartMs: nextSourceStartMs,
          durationMs: nextDurationMs
        });
      } else {
        const maxDurationMs = Math.max(
          1000,
          session.assetDurationMs - session.initialSourceStartMs
        );
        const nextDurationMs = snapToStep(
          Math.max(
            1000,
            Math.min(maxDurationMs, session.initialDurationMs + deltaMs)
          ),
          snapStepMs
        );
        onUpdateTimelineClip(session.clipId, {durationMs: nextDurationMs});
      }
    }

    function handlePointerUp() {
      setTrimSession(null);
    }

    window.addEventListener("mousemove", handlePointerMove);
    window.addEventListener("mouseup", handlePointerUp);
    return () => {
      window.removeEventListener("mousemove", handlePointerMove);
      window.removeEventListener("mouseup", handlePointerUp);
    };
  }, [onUpdateTimelineClip, trimSession]);

  useEffect(() => {
    if (playheadDragStartX === null) {
      return;
    }
    const dragOriginX = playheadDragStartX;

    function handlePointerMove(event: MouseEvent) {
      const offsetX = Math.max(0, Math.min(workspaceWidth, event.clientX - dragOriginX));
      const rawElapsedMs = Math.round((offsetX / pixelsPerSecond) * 1000);
      onSeekTimeline(snapToTimelinePoint(rawElapsedMs, timelineSnapPointsMs));
    }

    function handlePointerUp() {
      setPlayheadDragStartX(null);
    }

    window.addEventListener("mousemove", handlePointerMove);
    window.addEventListener("mouseup", handlePointerUp);
    return () => {
      window.removeEventListener("mousemove", handlePointerMove);
      window.removeEventListener("mouseup", handlePointerUp);
    };
  }, [onSeekTimeline, pixelsPerSecond, playheadDragStartX, timelineSnapPointsMs, workspaceWidth]);

  function toggleLaneControl(laneId: string, control: "locked" | "muted" | "visible") {
    setLaneControls((current) => ({
      ...current,
      [laneId]: {
        ...current[laneId],
        [control]: !current[laneId][control]
      }
    }));
  }

  return (
    <section
      style={{
        minHeight: 0,
        overflow: "hidden",
        background: "#0e1216",
        display: "grid",
        gridTemplateRows: "56px auto minmax(0, 1fr)"
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
          padding: "0 16px",
          borderBottom: "1px solid rgba(255,255,255,0.06)"
        }}
      >
        <div style={{display: "flex", alignItems: "center", gap: "12px"}}>
          <p style={sectionLabelStyle}>Editing Workspace</p>
        </div>
        <div style={{display: "flex", alignItems: "center", gap: "8px"}}>
          <button
            type="button"
            onClick={onToggleTimelinePlayback}
            style={toolbarButtonStyle}
          >
            {isTimelinePlaybackActive ? "Pause" : "Play"}
          </button>
          <button
            type="button"
            onClick={onSplitTimelineClip}
            disabled={!selectedTimelineClipId}
            style={{
              ...toolbarButtonStyle,
              opacity: selectedTimelineClipId ? 1 : 0.5,
              cursor: selectedTimelineClipId ? "pointer" : "default"
            }}
          >
            Split Clip
          </button>
        </div>
      </div>

      <div
        style={{
          padding: "10px 16px 12px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          background: "#11161c"
        }}
      >
        {selectedTimelineClip ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 1fr) minmax(240px, 340px)",
              alignItems: "center",
              gap: "20px",
              minWidth: 0
            }}
          >
            <div style={{minWidth: 0, display: "grid", gap: "4px"}}>
              <p
                style={{
                  ...textStyles.bodySmallStrong,
                  color: "#e7f2ff",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap"
                }}
                title={selectedTimelineAsset?.name ?? selectedTimelineClip.label}
              >
                {selectedTimelineAsset?.name ?? selectedTimelineClip.label}
              </p>
              <p style={{...textStyles.bodySmall, color: "#85919d", marginTop: "4px"}}>
                {formatDurationMs(selectedTimelineClip.durationMs)} · timeline{" "}
                {formatDurationMs(selectedTimelineClip.timelineStartMs)} · trim in{" "}
                {formatDurationMs(selectedTimelineClip.sourceStartMs)}
              </p>
            </div>
            <label style={{display: "grid", gap: "8px"}}>
              <div style={{display: "flex", justifyContent: "space-between", gap: "8px"}}>
                <span style={{...textStyles.bodySmall, color: "#74808c"}}>Timeline Scale</span>
                <span style={{...textStyles.bodySmall, color: "#dbe6f2"}}>
                  {formatTickLabel(activeZoomPreset.majorTickSeconds)}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={zoomPresets.length - 1}
                step={1}
                value={zoomPresetIndex}
                onChange={(event) => setZoomPresetIndex(Number(event.target.value))}
              />
            </label>
          </div>
        ) : (
          <div style={{display: "flex", alignItems: "center", gap: "12px", color: "#7f8b96"}}>
            <span style={sectionLabelStyle}>Timeline Ready</span>
            <span style={textStyles.bodySmall}>
              Drag clips into `V1`, use the scale slider, and drag clip edges to trim.
            </span>
          </div>
        )}
      </div>

      <div ref={timelineScrollRef} style={{minHeight: 0, overflow: "auto", background: "#0d1116"}}>
        <div style={{minWidth: `${workspaceWidth + 72}px`, minHeight: "100%"}}>
          <div
            style={{
              position: "sticky",
              top: 0,
              zIndex: 3,
              display: "grid",
              gridTemplateColumns: "72px minmax(0, 1fr)",
              background: "#141a20",
              borderBottom: "1px solid rgba(255,255,255,0.06)"
            }}
          >
            <div style={{borderRight: "1px solid rgba(255,255,255,0.06)"}} />
            <div
              style={{
                position: "relative",
                width: `${workspaceWidth}px`,
                height: "30px",
                background:
                  "linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0))"
              }}
            >
              {buildRulerTicks(
                workspaceDurationMs,
                pixelsPerSecond,
                activeZoomPreset.majorTickSeconds
              ).map((tick) => (
                <div
                  key={tick.label}
                  style={{
                    position: "absolute",
                    left: `${tick.left}px`,
                    top: 0,
                    bottom: 0,
                    width: "1px",
                    background: tick.major ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.06)"
                  }}
                >
                  {tick.major ? (
                    <span
                      style={{
                        position: "absolute",
                        top: "7px",
                        left: "6px",
                        color: "#798693",
                        fontSize: "10px",
                        whiteSpace: "nowrap"
                      }}
                    >
                      {tick.label}
                    </span>
                  ) : null}
                </div>
              ))}
              <div
                onMouseDown={(event) => {
                  const rect = event.currentTarget.parentElement?.getBoundingClientRect();
                  if (!rect) {
                    return;
                  }

                  setPlayheadDragStartX(rect.left);
                }}
                style={{
                  position: "absolute",
                  left: `${playheadLeft}px`,
                  top: 0,
                  bottom: "-176px",
                  width: "1px",
                  background: "rgba(255,88,88,0.9)",
                  boxShadow: "0 0 0 1px rgba(255,88,88,0.18)"
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    top: "2px",
                    left: "-4px",
                    width: "9px",
                    height: "9px",
                    borderRadius: "999px",
                    background: "#ff5a5a"
                  }}
                />
              </div>
            </div>
          </div>

          {lanes.map((lane) => (
            <div
              key={lane.id}
              style={{
                display: "grid",
                gridTemplateColumns: "72px minmax(0, 1fr)",
                borderBottom: "1px solid rgba(255,255,255,0.04)"
              }}
            >
              <div
                style={{
                  height: `${laneHeight}px`,
                  display: "grid",
                  gridTemplateColumns: "28px 1fr auto",
                  alignItems: "center",
                  gap: "4px",
                  padding: "0 6px",
                  color: "#7d8996",
                  fontSize: "12px",
                  borderRight: "1px solid rgba(255,255,255,0.06)",
                  background: "#131920"
                }}
              >
                <span
                  style={{
                    width: "16px",
                    height: "16px",
                    borderRadius: "5px",
                    display: "grid",
                    placeItems: "center",
                    background: "rgba(255,255,255,0.04)",
                    color: "#9aa6b3",
                    fontSize: "9px",
                    fontWeight: 700
                  }}
                >
                  {lane.label.startsWith("V") ? "V" : lane.label.startsWith("T") ? "T" : "A"}
                </span>
                <span style={{fontSize: "11px", color: "#aab5c0"}}>{lane.label}</span>
                <div style={{display: "flex", alignItems: "center", gap: "2px"}}>
                  <TrackControlButton
                    label="Visible"
                    active={laneControls[lane.id]?.visible ?? true}
                    onClick={() => toggleLaneControl(lane.id, "visible")}
                  >
                    {laneControls[lane.id]?.visible ? "O" : "X"}
                  </TrackControlButton>
                  <TrackControlButton
                    label="Lock"
                    active={laneControls[lane.id]?.locked ?? false}
                    onClick={() => toggleLaneControl(lane.id, "locked")}
                  >
                    {laneControls[lane.id]?.locked ? "L" : "-"}
                  </TrackControlButton>
                  <TrackControlButton
                    label="Mute"
                    active={laneControls[lane.id]?.muted ?? false}
                    onClick={() => toggleLaneControl(lane.id, "muted")}
                  >
                    {laneControls[lane.id]?.muted ? "M" : "~"}
                  </TrackControlButton>
                </div>
              </div>
              <div
                ref={lane.acceptsClips ? onTimelineDropZoneElementChange : undefined}
                data-timeline-dropzone={lane.acceptsClips ? "true" : undefined}
                onClick={(event) => {
                  if (!lane.acceptsClips) {
                    return;
                  }

                  const rect = event.currentTarget.getBoundingClientRect();
                  const offsetX = event.clientX - rect.left;
                  const rawElapsedMs = Math.round((offsetX / pixelsPerSecond) * 1000);
                  onSeekTimeline(snapToTimelinePoint(rawElapsedMs, timelineSnapPointsMs));
                }}
                onDragEnter={(event) => {
                  if (lane.acceptsClips) {
                    event.preventDefault();
                  }
                }}
                onDragOver={(event) => {
                  if (lane.acceptsClips) {
                    event.preventDefault();
                    event.dataTransfer.dropEffect = "copy";
                  }
                }}
                onDrop={(event) => {
                  if (!lane.acceptsClips) {
                    return;
                  }

                  event.preventDefault();
                  const assetId = readDraggedAssetId(event.dataTransfer);
                  const clipId = event.dataTransfer.getData("application/x-capcutai-timeline-clip");
                  const dropElapsedMs = getElapsedMsFromClientX(event.clientX);
                  if (assetId) {
                    onAddAssetToTimeline(assetId, dropElapsedMs);
                  } else if (clipId) {
                    onMoveTimelineClip(clipId, dropElapsedMs);
                  }
                }}
                style={{
                  position: "relative",
                  width: `${workspaceWidth}px`,
                  height: `${laneHeight}px`,
                  background:
                    laneControls[lane.id]?.visible === false
                      ? "#0b0f13"
                      : lane.acceptsClips
                      ? "#11161c"
                      : "#0f1419",
                  opacity: laneControls[lane.id]?.visible === false ? 0.45 : 1
                }}
              >
                {lane.acceptsClips
                  ? timelineClips.map((clip) => {
                      if (laneControls[lane.id]?.locked) {
                        return null;
                      }
                      const asset = assetMap.get(clip.assetId);
                      const left = Math.round((clipOffsets[clip.clipId] / 1000) * pixelsPerSecond);
                      const width = Math.max(
                        48,
                        Math.round((clip.durationMs / 1000) * pixelsPerSecond)
                      );

                      return (
                        <button
                          key={clip.clipId}
                          type="button"
                          onMouseDown={(event) => {
                            if (event.button !== 0) {
                              return;
                            }

                            if (laneControls[lane.id]?.locked) {
                              return;
                            }
                            setDraggingTimelineClipId(clip.clipId);
                            setClipDragSession({
                              clipId: clip.clipId,
                              startX: event.clientX,
                              initialTimelineStartMs: clip.timelineStartMs
                            });
                          }}
                          onMouseUp={() => setDraggingTimelineClipId(null)}
                          onClick={() => onSelectTimelineClip(clip.clipId)}
                          style={{
                            position: "absolute",
                            left: `${left}px`,
                            top: "5px",
                            width: `${width}px`,
                            height: `${laneHeight - 10}px`,
                            appearance: "none",
                            border:
                              selectedTimelineClipId === clip.clipId
                                ? "1px solid rgba(121,192,255,0.64)"
                                : "1px solid rgba(255,255,255,0.08)",
                            borderRadius: "8px",
                            background:
                              selectedTimelineClipId === clip.clipId
                                ? "linear-gradient(180deg, #3890c9 0%, #2d6d95 100%)"
                                : draggingTimelineClipId === clip.clipId
                                ? "#316885"
                                : "linear-gradient(180deg, #2d6d95 0%, #275b7a 100%)",
                            color: "#f4f8fb",
                            padding: "0 10px",
                            textAlign: "left",
                            cursor: laneControls[lane.id]?.locked
                              ? "default"
                              : draggingTimelineClipId === clip.clipId
                              ? "grabbing"
                              : "grab",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            fontSize: "11px",
                            fontWeight: 600
                          }}
                          title={`${asset?.name ?? clip.label} · ${formatDurationMs(clip.durationMs)}`}
                        >
                          <span
                            onMouseDown={(event) => {
                              event.preventDefault();
                              event.stopPropagation();
                              if (laneControls[lane.id]?.locked) {
                                return;
                              }
                              setTrimSession({
                                clipId: clip.clipId,
                                edge: "start",
                                startX: event.clientX,
                                initialSourceStartMs: clip.sourceStartMs,
                                initialDurationMs: clip.durationMs,
                                assetDurationMs: Math.max(
                                  1000,
                                  Math.round((asset?.durationSeconds ?? 0) * 1000)
                                )
                              });
                            }}
                            style={{
                              position: "absolute",
                              left: 0,
                              top: 0,
                              bottom: 0,
                              width: "8px",
                              cursor: "ew-resize",
                              background: "rgba(255,255,255,0.22)"
                            }}
                          />
                          {asset?.name ?? clip.label}
                          <span
                            onMouseDown={(event) => {
                              event.preventDefault();
                              event.stopPropagation();
                              if (laneControls[lane.id]?.locked) {
                                return;
                              }
                              setTrimSession({
                                clipId: clip.clipId,
                                edge: "end",
                                startX: event.clientX,
                                initialSourceStartMs: clip.sourceStartMs,
                                initialDurationMs: clip.durationMs,
                                assetDurationMs: Math.max(
                                  1000,
                                  Math.round((asset?.durationSeconds ?? 0) * 1000)
                                )
                              });
                            }}
                            style={{
                              position: "absolute",
                              right: 0,
                              top: 0,
                              bottom: 0,
                              width: "8px",
                              cursor: "ew-resize",
                              background: "rgba(255,255,255,0.22)"
                            }}
                          />
                        </button>
                      );
                    })
                  : null}
                {lane.acceptsClips ? (
                  <div
                    style={{
                      position: "absolute",
                      left: `${playheadLeft}px`,
                      top: 0,
                      bottom: 0,
                      width: "1px",
                      background: "rgba(255,88,88,0.9)",
                      pointerEvents: "none"
                    }}
                  />
                ) : null}
                {lane.acceptsClips && insertionIndicatorMs !== null ? (
                  <div
                    style={{
                      position: "absolute",
                      left: `${Math.round((insertionIndicatorMs / 1000) * pixelsPerSecond)}px`,
                      top: 0,
                      bottom: 0,
                      width: "2px",
                      background: "rgba(121,192,255,0.95)",
                      boxShadow: "0 0 0 1px rgba(121,192,255,0.18), 0 0 16px rgba(121,192,255,0.28)",
                      pointerEvents: "none",
                      zIndex: 2
                    }}
                  >
                    <span
                      style={{
                        position: "absolute",
                        top: "4px",
                        left: "8px",
                        padding: "3px 6px",
                        borderRadius: "999px",
                        background: "rgba(16,22,28,0.96)",
                        border: "1px solid rgba(121,192,255,0.32)",
                        color: "#dff1ff",
                        fontSize: "10px",
                        whiteSpace: "nowrap"
                      }}
                    >
                      {externalTimelineDrag ? "Drop at " : "Snap "} {formatDurationMs(insertionIndicatorMs)}
                    </span>
                  </div>
                ) : null}
                {lane.acceptsClips
                  ? timelineSnapPointsMs.map((snapPointMs) => (
                      <div
                        key={`${lane.id}_${snapPointMs}`}
                        style={{
                          position: "absolute",
                          left: `${Math.round((snapPointMs / 1000) * pixelsPerSecond)}px`,
                          top: 0,
                          bottom: 0,
                          width: "1px",
                          background: "rgba(121,192,255,0.10)",
                          pointerEvents: "none"
                        }}
                      />
                    ))
                  : null}
                {lane.acceptsClips && timelineClips.length === 0 ? (
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      display: "grid",
                      placeItems: "center",
                      color: "#5f6c79",
                      fontSize: "12px"
                    }}
                  >
                    Drop clips anywhere on `V1`
                  </div>
                ) : null}
                {lane.acceptsClips && isTimelinePlaybackActive ? (
                  <div
                    style={{
                      position: "absolute",
                      left: "8px",
                      bottom: "4px",
                      color: "#ff8f8f",
                      fontSize: "10px",
                      pointerEvents: "none"
                    }}
                  >
                    Playing
                  </div>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function SliderField({
  label,
  min,
  max,
  value,
  valueLabel,
  onChange
}: {
  label: string;
  min: number;
  max: number;
  value: number;
  valueLabel: string;
  onChange: (nextValue: number) => void;
}) {
  return (
    <label style={{display: "grid", gap: "6px"}}>
      <div style={{display: "flex", justifyContent: "space-between", gap: "8px"}}>
        <span style={{...textStyles.bodySmall, color: "#85919d"}}>{label}</span>
        <span style={{...textStyles.bodySmall, color: "#dce7f2"}}>{valueLabel}</span>
      </div>
      <input
        type="range"
        min={min}
        max={Math.max(min, max)}
        value={Math.min(Math.max(min, value), Math.max(min, max))}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function TrackControlButton({
  label,
  active,
  onClick,
  children
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  children: string;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      style={{
        appearance: "none",
        border: "1px solid rgba(255,255,255,0.08)",
        background: active ? "rgba(121,192,255,0.16)" : "rgba(255,255,255,0.03)",
        color: active ? "#dcecff" : "#75818d",
        borderRadius: "5px",
        width: "18px",
        height: "18px",
        padding: 0,
        fontSize: "9px",
        lineHeight: 1,
        cursor: "pointer"
      }}
    >
      {children}
    </button>
  );
}

function buildRulerTicks(durationMs: number, pixelsPerSecond: number, majorTickSeconds: number) {
  const totalSeconds = Math.ceil(durationMs / 1000);
  const minorTickSeconds = Math.max(1, Math.floor(majorTickSeconds / 5));
  const tickCount = Math.ceil(totalSeconds / minorTickSeconds);

  return Array.from({length: tickCount + 1}, (_, index) => {
    const seconds = index * minorTickSeconds;
    return {
      left: seconds * pixelsPerSecond,
      major: seconds % majorTickSeconds === 0,
      label: formatTimecode(seconds)
    };
  });
}

function formatTimecode(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function formatDurationMs(durationMs: number) {
  const totalSeconds = Math.max(0, Math.round(durationMs / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  if (minutes <= 0) {
    return `${seconds}s`;
  }

  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function formatTickLabel(seconds: number) {
  if (seconds < 60) {
    return `${seconds}s`;
  }

  const minutes = Math.floor(seconds / 60);
  return `${minutes}m`;
}

function snapToStep(valueMs: number, stepMs: number) {
  return Math.round(valueMs / stepMs) * stepMs;
}

function snapToTimelinePoint(valueMs: number, snapPointsMs: number[]) {
  const steppedValueMs = snapToStep(valueMs, snapStepMs);
  let bestValueMs = steppedValueMs;
  let bestDistanceMs = Number.POSITIVE_INFINITY;

  for (const snapPointMs of snapPointsMs) {
    const distanceMs = Math.abs(snapPointMs - valueMs);
    if (distanceMs < bestDistanceMs && distanceMs <= 240) {
      bestDistanceMs = distanceMs;
      bestValueMs = snapPointMs;
    }
  }

  return bestValueMs;
}

function timelineZoomButtonStyle(isActive: boolean) {
  return {
    appearance: "none",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: "999px",
    background: isActive ? "rgba(121,192,255,0.16)" : "#171c21",
    color: isActive ? "#dcecff" : "#8a97a3",
    padding: "4px 8px",
    cursor: "pointer",
    fontSize: "10px",
    fontWeight: 700,
    lineHeight: 1
  } as const;
}

const toolbarButtonStyle = {
  appearance: "none",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "10px",
  background: "#181d22",
  color: "#dbe4ed",
  padding: "8px 10px",
  cursor: "pointer",
  ...textStyles.iconButton
} as const;
