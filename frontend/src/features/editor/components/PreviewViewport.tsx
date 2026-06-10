import {useEffect, useMemo, useRef, useState} from "react";
import {textStyles} from "../../../shared/design/typography";
import type {AssetItem} from "../../assets/types/assets";
import type {EditingExperience, SourceMaterial, WorkspaceTimelineClip} from "../types/editor-preview";

type PreviewViewportProps = {
  title: string;
  subtitle?: string;
  previewMode: "asset" | "timeline";
  timelineAssets: AssetItem[];
  timelineClips: WorkspaceTimelineClip[];
  selectedTimelineClipId: string | null;
  timelineElapsedMs: number;
  isTimelinePlaybackActive: boolean;
  onTimelineElapsedMsChange: (elapsedMs: number) => void;
  onTimelinePlaybackActiveChange: (isActive: boolean) => void;
  onActiveTimelineClipChange: (clipId: string | null) => void;
  onRequestTimelinePreview: () => void;
  selectedPreviewAsset: AssetItem | null;
  selectedSourceAsset: AssetItem | null;
  sourceAssetCount: number;
  editingExperience: EditingExperience;
  sourceMaterials: SourceMaterial[];
  previewSource?: {
    objectUrl?: string;
    name: string;
    mimeType: string;
  } | null;
};

const sectionLabelStyle = textStyles.sectionLabel;
type PreviewScaleMode = "contain" | "cover";
const previewContentPaddingPx = 20;
const timelineControlsReservedHeightPx = 56;

export function PreviewViewport({
  title,
  subtitle,
  previewSource,
  previewMode,
  timelineAssets,
  timelineClips,
  selectedTimelineClipId,
  timelineElapsedMs,
  isTimelinePlaybackActive,
  onTimelineElapsedMsChange,
  onTimelinePlaybackActiveChange,
  onActiveTimelineClipChange,
  onRequestTimelinePreview,
  selectedPreviewAsset,
  selectedSourceAsset,
  sourceAssetCount,
  editingExperience,
  sourceMaterials
}: PreviewViewportProps) {
  const [previewScaleMode, setPreviewScaleMode] = useState<PreviewScaleMode>("contain");
  const [activeTimelineClipId, setActiveTimelineClipId] = useState<string | null>(null);
  const previewFrameRef = useRef<HTMLDivElement>(null);
  const timelineVideoRef = useRef<HTMLVideoElement>(null);
  const [previewFrameSize, setPreviewFrameSize] = useState({width: 0, height: 0});
  const orderedTimelineClips = useMemo(
    () => [...timelineClips].sort((left, right) => left.timelineStartMs - right.timelineStartMs),
    [timelineClips]
  );
  const timelineDurationMs = orderedTimelineClips.reduce(
    (maxDurationMs, clip) => Math.max(maxDurationMs, clip.timelineStartMs + clip.durationMs),
    0
  );
  const activeTimelineClip =
    orderedTimelineClips.find((clip) => clip.clipId === activeTimelineClipId) ??
    orderedTimelineClips.find((clip) => clip.clipId === selectedTimelineClipId) ??
    orderedTimelineClips.find(
      (clip) =>
        timelineElapsedMs >= clip.timelineStartMs &&
        timelineElapsedMs < clip.timelineStartMs + clip.durationMs
    ) ??
    orderedTimelineClips[0] ??
    null;
  const activeTimelineAsset = activeTimelineClip
    ? timelineAssets.find((asset) => asset.assetId === activeTimelineClip.assetId) ?? null
    : null;
  const isTimelinePreviewVisible =
    previewMode === "timeline" && Boolean(activeTimelineClip && activeTimelineAsset?.objectUrl);
  const mediaAspectRatio =
    isTimelinePreviewVisible && activeTimelineAsset?.frameWidth && activeTimelineAsset?.frameHeight
      ? activeTimelineAsset.frameWidth / activeTimelineAsset.frameHeight
      : selectedPreviewAsset?.frameWidth && selectedPreviewAsset?.frameHeight
      ? selectedPreviewAsset.frameWidth / selectedPreviewAsset.frameHeight
      : 16 / 9;

  useEffect(() => {
    if (!orderedTimelineClips.length) {
      onTimelinePlaybackActiveChange(false);
      setActiveTimelineClipId(null);
      onTimelineElapsedMsChange(0);
      return;
    }

    if (selectedTimelineClipId) {
      setActiveTimelineClipId(selectedTimelineClipId);
    }
  }, [onTimelineElapsedMsChange, onTimelinePlaybackActiveChange, orderedTimelineClips, selectedTimelineClipId]);

  useEffect(() => {
    const element = previewFrameRef.current;
    if (!element) {
      return;
    }

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) {
        return;
      }

      const {width, height} = entry.contentRect;
      setPreviewFrameSize({
        width: Math.max(0, width),
        height: Math.max(0, height)
      });
    });

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, []);

  const previewBoxStyle = useMemo(() => {
    const frameWidth = Math.max(0, previewFrameSize.width - previewContentPaddingPx * 2);
    const frameHeight = Math.max(
      0,
      previewFrameSize.height -
        previewContentPaddingPx * 2 -
        (isTimelinePreviewVisible ? timelineControlsReservedHeightPx : 0)
    );

    if (!frameWidth || !frameHeight) {
      return {
        width: "100%",
        height: "100%",
        maxWidth: "100%",
        maxHeight: "100%"
      };
    }

    const frameAspectRatio = frameWidth / frameHeight;

    if (previewScaleMode === "cover") {
      if (frameAspectRatio > mediaAspectRatio) {
        return {
          width: `${frameWidth}px`,
          height: `${frameWidth / mediaAspectRatio}px`,
          maxWidth: "100%",
          maxHeight: "100%"
        };
      }

      return {
        width: `${frameHeight * mediaAspectRatio}px`,
        height: `${frameHeight}px`,
        maxWidth: "100%",
        maxHeight: "100%"
      };
    }

    if (frameAspectRatio > mediaAspectRatio) {
      return {
        width: `${frameHeight * mediaAspectRatio}px`,
        height: `${frameHeight}px`,
        maxWidth: "100%",
        maxHeight: "100%"
      };
    }

    return {
      width: `${frameWidth}px`,
      height: `${frameWidth / mediaAspectRatio}px`,
      maxWidth: "100%",
      maxHeight: "100%"
    };
  }, [
    isTimelinePreviewVisible,
    mediaAspectRatio,
    previewFrameSize.height,
    previewFrameSize.width,
    previewScaleMode
  ]);

  useEffect(() => {
    const video = timelineVideoRef.current;
    if (!video || !isTimelinePreviewVisible || !activeTimelineClip || !activeTimelineAsset?.objectUrl) {
      return;
    }

    const clipOffsetMs = Math.max(0, timelineElapsedMs - activeTimelineClip.timelineStartMs);
    const targetTimeSeconds =
      (activeTimelineClip.sourceStartMs + Math.min(activeTimelineClip.durationMs, clipOffsetMs)) /
      1000;

    const syncFrame = () => {
      if (Math.abs(video.currentTime - targetTimeSeconds) > 0.05) {
        video.currentTime = targetTimeSeconds;
      }
    };

    if (video.readyState >= HTMLMediaElement.HAVE_METADATA) {
      syncFrame();
      return;
    }

    video.addEventListener("loadedmetadata", syncFrame);
    return () => {
      video.removeEventListener("loadedmetadata", syncFrame);
    };
  }, [
    activeTimelineAsset?.objectUrl,
    activeTimelineClip,
    isTimelinePreviewVisible,
    timelineElapsedMs
  ]);

  useEffect(() => {
    const video = timelineVideoRef.current;
    if (!video || !isTimelinePreviewVisible || !activeTimelineClip || !activeTimelineAsset?.objectUrl) {
      return;
    }

    if (!isTimelinePlaybackActive) {
      video.pause();
      return;
    }

    const onLoadedMetadata = async () => {
      try {
        await video.play();
      } catch {
        onTimelinePlaybackActiveChange(false);
      }
    };

    const onTimeUpdate = () => {
      const clipEndSeconds =
        (activeTimelineClip.sourceStartMs + activeTimelineClip.durationMs) / 1000;
      const localElapsedMs = Math.max(
        0,
        Math.round((video.currentTime - activeTimelineClip.sourceStartMs / 1000) * 1000)
      );
      onTimelineElapsedMsChange(
        Math.min(timelineDurationMs, activeTimelineClip.timelineStartMs + localElapsedMs)
      );

      if (video.currentTime >= clipEndSeconds) {
        const currentIndex = orderedTimelineClips.findIndex(
          (clip) => clip.clipId === activeTimelineClip.clipId
        );
        const nextClip = orderedTimelineClips[currentIndex + 1];
        if (nextClip) {
          setActiveTimelineClipId(nextClip.clipId);
          onActiveTimelineClipChange(nextClip.clipId);
          onTimelineElapsedMsChange(nextClip.timelineStartMs);
        } else {
          onTimelinePlaybackActiveChange(false);
          onTimelineElapsedMsChange(timelineDurationMs);
          video.pause();
        }
      }
    };

    video.addEventListener("loadedmetadata", onLoadedMetadata);
    video.addEventListener("timeupdate", onTimeUpdate);
    if (video.readyState >= HTMLMediaElement.HAVE_METADATA) {
      void onLoadedMetadata();
    }

    return () => {
      video.removeEventListener("loadedmetadata", onLoadedMetadata);
      video.removeEventListener("timeupdate", onTimeUpdate);
    };
  }, [
    activeTimelineAsset?.objectUrl,
    activeTimelineClip,
    isTimelinePlaybackActive,
    isTimelinePreviewVisible,
    onActiveTimelineClipChange,
    onTimelineElapsedMsChange,
    onTimelinePlaybackActiveChange,
    orderedTimelineClips,
    timelineDurationMs
  ]);

  return (
    <section
      style={{
        minHeight: 0,
        overflow: "hidden",
        background: "#121518",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        display: "grid",
        gridTemplateRows: "56px minmax(0, 1fr)"
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "12px",
          padding: "0 16px",
          borderBottom: "1px solid rgba(255,255,255,0.06)"
        }}
      >
        <p style={sectionLabelStyle}>Preview</p>
        <div style={{display: "flex", alignItems: "center", gap: "8px"}}>
          <ScaleToggleButton
            label="Fit"
            active={previewScaleMode === "contain"}
            onClick={() => setPreviewScaleMode("contain")}
          />
          <ScaleToggleButton
            label="Fill"
            active={previewScaleMode === "cover"}
            onClick={() => setPreviewScaleMode("cover")}
          />
        </div>
      </div>
      <div
        style={{
          minHeight: 0,
          display: "grid",
          gridTemplateRows: "minmax(0, 1fr)",
          overflow: "hidden",
          background: "#0d1013"
        }}
      >
        <div
          style={{
            minHeight: 0,
            padding: "16px",
            display: "grid"
          }}
        >
          <div
            ref={previewFrameRef}
            style={{
              minHeight: 0,
              borderRadius: "18px",
              background:
                "radial-gradient(circle at top right, rgba(255,153,102,0.18), transparent 24%), #0b0e11",
              border: "1px solid rgba(255,255,255,0.06)",
              overflow: "hidden",
              display: "grid",
              placeItems: "center"
            }}
          >
            {isTimelinePreviewVisible && activeTimelineClip && activeTimelineAsset?.objectUrl ? (
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  display: "grid",
                  gridTemplateRows: "minmax(0, 1fr) auto",
                  padding: `${previewContentPaddingPx}px`,
                  boxSizing: "border-box",
                  gap: "12px"
                }}
              >
                <div
                  style={{
                    minWidth: 0,
                    minHeight: 0,
                    display: "grid",
                    placeItems: "center",
                    overflow: "hidden"
                  }}
                >
                  <div
                    style={{
                      ...previewBoxStyle,
                      minWidth: 0,
                      minHeight: 0,
                      overflow: "hidden",
                      borderRadius: "14px",
                      background: "#090b0d",
                      display: "grid",
                      placeItems: "center"
                    }}
                  >
                    <video
                      ref={timelineVideoRef}
                      key={`${activeTimelineAsset.objectUrl}_${activeTimelineClip.clipId}`}
                      src={activeTimelineAsset.objectUrl}
                      playsInline
                      preload="metadata"
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: previewScaleMode,
                        objectPosition: "center center",
                        background: "#090b0d",
                        display: "block"
                      }}
                    />
                  </div>
                </div>
                <TimelinePlaybackBar
                  clip={activeTimelineClip}
                  isPlaying={isTimelinePlaybackActive}
                  elapsedMs={timelineElapsedMs}
                  totalDurationMs={timelineDurationMs}
                  onToggle={() => {
                    if (!orderedTimelineClips.length) {
                      return;
                    }

                    onRequestTimelinePreview();
                    if (!isTimelinePlaybackActive && !activeTimelineClipId) {
                      setActiveTimelineClipId(orderedTimelineClips[0]?.clipId ?? null);
                      onActiveTimelineClipChange(orderedTimelineClips[0]?.clipId ?? null);
                    }
                    onTimelinePlaybackActiveChange(!isTimelinePlaybackActive);
                  }}
                />
              </div>
            ) : previewSource?.objectUrl ? (
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  display: "grid",
                  placeItems: "center",
                  padding: `${previewContentPaddingPx}px`,
                  boxSizing: "border-box",
                  overflow: "hidden"
                }}
              >
                <div
                  style={{
                    ...previewBoxStyle,
                    minWidth: 0,
                    minHeight: 0,
                    overflow: "hidden",
                    borderRadius: "14px",
                    background: "#090b0d",
                    display: "grid",
                    placeItems: "center"
                  }}
                >
                  <video
                    key={previewSource.objectUrl}
                    src={previewSource.objectUrl}
                    controls
                    playsInline
                    preload="metadata"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: previewScaleMode,
                      objectPosition: "center center",
                      background: "#090b0d",
                      display: "block"
                    }}
                  />
                </div>
              </div>
            ) : (
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  display: "grid",
                  placeItems: "center",
                  textAlign: "center",
                  padding: "24px"
                }}
              >
                <div style={{textAlign: "center", maxWidth: "520px"}}>
                  <p style={{...sectionLabelStyle, color: "#98a5b2"}}>Live Preview</p>
                  <div
                    style={{
                      width: "56px",
                      height: "56px",
                      margin: "14px auto 0",
                      borderRadius: "16px",
                      background: "rgba(121,192,255,0.08)",
                      color: "#89beff",
                      display: "grid",
                      placeItems: "center",
                      fontSize: "22px",
                      fontWeight: 700
                    }}
                  >
                    ▶
                  </div>
                  <p
                    style={{
                      ...textStyles.display,
                      fontSize: "clamp(15px, 1.4vw, 17px)",
                      margin: "16px 0 0"
                    }}
                  >
                    上传视频后，这里会立即显示预览。
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function ScaleToggleButton({
  label,
  active,
  onClick
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        appearance: "none",
        border: "1px solid rgba(255,255,255,0.08)",
        background: active ? "rgba(121,192,255,0.16)" : "#151a1f",
        color: active ? "#dcecff" : "#94a0ac",
        borderRadius: "999px",
        padding: "6px 10px",
        cursor: "pointer",
        fontSize: "11px",
        fontWeight: 600,
        lineHeight: 1
      }}
    >
      {label}
    </button>
  );
}

function TimelinePlaybackBar({
  clip,
  isPlaying,
  elapsedMs,
  totalDurationMs,
  onToggle
}: {
  clip: WorkspaceTimelineClip;
  isPlaying: boolean;
  elapsedMs: number;
  totalDurationMs: number;
  onToggle: () => void;
}) {
  const progress =
    totalDurationMs > 0 ? Math.max(0, Math.min(100, (elapsedMs / totalDurationMs) * 100)) : 0;

  return (
    <div
      style={{
        borderRadius: "12px",
        border: "1px solid rgba(255,255,255,0.06)",
        background: "#10161b",
        padding: "10px 12px",
        display: "grid",
        gap: "10px"
      }}
    >
      <div style={{display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px"}}>
        <button
          type="button"
          onClick={onToggle}
          style={{
            appearance: "none",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "999px",
            background: "rgba(121,192,255,0.16)",
            color: "#dcecff",
            padding: "6px 12px",
            cursor: "pointer",
            fontSize: "11px",
            fontWeight: 600,
            lineHeight: 1
          }}
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
        <span style={{...textStyles.bodySmall, color: "#dbe4ed"}}>{clip.label}</span>
        <span style={{...textStyles.bodySmall, color: "#8a96a2"}}>
          {formatDurationMs(elapsedMs)} / {formatDurationMs(totalDurationMs)}
        </span>
      </div>
      <div
        style={{
          height: "8px",
          borderRadius: "999px",
          background: "#0a0d10",
          overflow: "hidden"
        }}
      >
        <div
          style={{
            width: `${progress}%`,
            height: "100%",
            background: "linear-gradient(90deg, #4b88ad 0%, #80cfff 100%)"
          }}
        />
      </div>
    </div>
  );
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
