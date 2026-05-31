import {useEffect, useMemo, useRef, useState} from "react";
import {textStyles} from "../../../shared/design/typography";
import type {AssetItem} from "../../assets/types/assets";
import type {EditingExperience, SourceMaterial} from "../types/editor-preview";

type PreviewViewportProps = {
  title: string;
  subtitle?: string;
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

export function PreviewViewport({
  title,
  subtitle,
  previewSource,
  selectedSourceAsset,
  sourceAssetCount,
  editingExperience,
  sourceMaterials
}: PreviewViewportProps) {
  const sourceMaterialCount = sourceMaterials.length;
  const totalShotCount = sourceMaterials.reduce(
    (total, sourceMaterial) => total + sourceMaterial.visualShots.length,
    0
  );
  const totalSentenceCount = sourceMaterials.reduce(
    (total, sourceMaterial) => total + sourceMaterial.transcript.sentences.length,
    0
  );
  const totalDropCount = sourceMaterials.reduce(
    (total, sourceMaterial) => total + sourceMaterial.dropsMs.length,
    0
  );
  const [previewScaleMode, setPreviewScaleMode] = useState<PreviewScaleMode>("contain");
  const previewFrameRef = useRef<HTMLDivElement>(null);
  const [previewFrameSize, setPreviewFrameSize] = useState({width: 0, height: 0});
  const mediaAspectRatio =
    selectedSourceAsset?.frameWidth && selectedSourceAsset?.frameHeight
      ? selectedSourceAsset.frameWidth / selectedSourceAsset.frameHeight
      : 16 / 9;

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
    const frameWidth = previewFrameSize.width;
    const frameHeight = previewFrameSize.height;

    if (!frameWidth || !frameHeight) {
      return {
        width: "100%",
        height: "100%"
      };
    }

    const frameAspectRatio = frameWidth / frameHeight;

    if (previewScaleMode === "cover") {
      if (frameAspectRatio > mediaAspectRatio) {
        return {
          width: `${frameWidth}px`,
          height: `${frameWidth / mediaAspectRatio}px`
        };
      }

      return {
        width: `${frameHeight * mediaAspectRatio}px`,
        height: `${frameHeight}px`
      };
    }

    if (frameAspectRatio > mediaAspectRatio) {
      return {
        width: `${frameHeight * mediaAspectRatio}px`,
        height: `${frameHeight}px`
      };
    }

    return {
      width: `${frameWidth}px`,
      height: `${frameWidth / mediaAspectRatio}px`
    };
  }, [mediaAspectRatio, previewFrameSize.height, previewFrameSize.width, previewScaleMode]);
  const sourceMaterialSummary =
    sourceMaterialCount > 0
      ? sourceMaterials.map((sourceMaterial) => sourceMaterial.sourceCaseId.slice(0, 8)).join(" / ")
      : "No source material";

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
          gridTemplateRows: "minmax(0, 1fr) auto",
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
            {previewSource?.objectUrl ? (
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  display: "grid",
                  placeItems: "center",
                  padding: "20px",
                  overflow: "hidden"
                }}
              >
                <div
                  style={{
                    ...previewBoxStyle,
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

        <div
          style={{
            borderTop: "1px solid rgba(255,255,255,0.06)",
            background: "#101316",
            padding: "12px 16px 14px",
            display: "grid",
            gridAutoFlow: "column",
            gridAutoColumns: "minmax(180px, 1fr)",
            gap: "10px",
            overflowX: "auto",
            overflowY: "hidden"
          }}
        >
          <InspectorTile
            label="Source Assets"
            value={`${sourceAssetCount} video${sourceAssetCount === 1 ? "" : "s"}`}
            detail={selectedSourceAsset ? formatAssetMeta(selectedSourceAsset) : "Waiting for upload"}
          />
          <InspectorTile
            label="Current Preview"
            value={selectedSourceAsset?.name ?? "No video selected"}
            detail={selectedSourceAsset?.mimeType ?? "Select a source video"}
          />
          <InspectorTile
            label="Source Materials"
            value={`${sourceMaterialCount} case${sourceMaterialCount === 1 ? "" : "s"}`}
            detail={`${totalShotCount} shots · ${totalSentenceCount} sentences`}
          />
          <InspectorTile
            label="Editing Experience"
            value={editingExperience.styleName}
            detail={`${editingExperience.storylinePhases.length} phases · ${totalDropCount} drops`}
          />
          <InspectorTile
            label="Mock Cases"
            value={sourceMaterialSummary}
            detail="Audio / transcript / visual analyzer output"
          />
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

function InspectorTile({label, value, detail}: {label: string; value: string; detail: string}) {
  return (
    <div
      style={{
        minWidth: 0,
        borderRadius: "12px",
        border: "1px solid rgba(255,255,255,0.06)",
        background: "#14181c",
        padding: "10px 12px"
      }}
    >
      <p style={sectionLabelStyle}>{label}</p>
      <p
        style={{
          ...textStyles.titleSmall,
          marginTop: "6px",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap"
        }}
        title={value}
      >
        {value}
      </p>
      <p
        style={{
          ...textStyles.bodySmall,
          marginTop: "4px",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          fontSize: "11px"
        }}
        title={detail}
      >
        {detail}
      </p>
    </div>
  );
}

function formatAssetMeta(asset: AssetItem) {
  const parts = [formatBytes(asset.sizeBytes)];

  if (asset.frameWidth && asset.frameHeight) {
    parts.push(`${asset.frameWidth}x${asset.frameHeight}`);
  }

  if (asset.durationSeconds) {
    parts.push(formatDuration(asset.durationSeconds));
  }

  return parts.join(" · ");
}

function formatBytes(sizeBytes: number) {
  if (sizeBytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(sizeBytes / 1024))} KB`;
  }

  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(durationSeconds: number) {
  const minutes = Math.floor(durationSeconds / 60);
  const seconds = Math.max(0, Math.round(durationSeconds % 60));

  if (minutes <= 0) {
    return `${seconds}s`;
  }

  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
}
