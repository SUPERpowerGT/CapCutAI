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
        gridTemplateRows: "56px minmax(0, 1fr) auto"
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "0 16px",
          borderBottom: "1px solid rgba(255,255,255,0.06)"
        }}
      >
        <p style={sectionLabelStyle}>Preview</p>
      </div>
      <div
        style={{
          minHeight: 0,
          borderRadius: "18px",
          background:
            "radial-gradient(circle at top right, rgba(255,153,102,0.18), transparent 24%), #0d1013",
          padding: "16px",
          display: "grid",
          placeItems: "center",
          overflow: "hidden"
        }}
      >
        {previewSource?.objectUrl ? (
          <div
            style={{
              aspectRatio: "16 / 9",
              width: "100%",
              maxWidth: "100%",
              maxHeight: "100%",
              borderRadius: "16px",
              overflow: "hidden",
              background: "#090b0d",
              border: "1px solid rgba(255,255,255,0.06)",
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
                objectFit: "contain",
                background: "#090b0d"
              }}
            />
          </div>
        ) : (
          <div
            style={{
              aspectRatio: "16 / 9",
              width: "100%",
              maxWidth: "100%",
              maxHeight: "100%",
              display: "grid",
              placeItems: "center",
              textAlign: "center",
              padding: "20px"
            }}
          >
            <div style={{textAlign: "center", maxWidth: "520px"}}>
              <p style={{...sectionLabelStyle, color: "#98a5b2"}}>Live Preview</p>
              <div
                style={{
                  width: "48px",
                  height: "48px",
                  margin: "12px auto 0",
                  borderRadius: "14px",
                  background: "rgba(121,192,255,0.08)",
                  color: "#89beff",
                  display: "grid",
                  placeItems: "center",
                  fontSize: "20px",
                  fontWeight: 700
                }}
              >
                ▶
              </div>
              <p
                style={{
                  ...textStyles.display,
                  margin: "16px 0 0"
                }}
              >
                上传视频后，这里会立即显示预览。
              </p>
            </div>
          </div>
        )}
      </div>
      <div
        style={{
          borderTop: "1px solid rgba(255,255,255,0.06)",
          background: "#101316",
          padding: "12px 16px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "12px"
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
    </section>
  );
}

function InspectorTile({label, value, detail}: {label: string; value: string; detail: string}) {
  return (
    <div
      style={{
        minWidth: 0,
        borderRadius: "10px",
        border: "1px solid rgba(255,255,255,0.06)",
        background: "#14181c",
        padding: "10px"
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
          whiteSpace: "nowrap"
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
