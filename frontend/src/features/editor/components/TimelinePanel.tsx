import {textStyles} from "../../../shared/design/typography";
import type {AssetItem} from "../../assets/types/assets";
import type {
  EditingExperience,
  EditingJob,
  EditorExportPackage,
  SourceMaterial,
  TimelinePlan
} from "../types/editor-preview";

type TimelinePanelProps = {
  sourceAssets: AssetItem[];
  editingExperience: EditingExperience;
  sourceMaterials: SourceMaterial[];
  timelinePlan: TimelinePlan;
  editingJob: EditingJob;
  lastExportPackage: EditorExportPackage | null;
  onExportEditingPackage: () => void;
};

const sectionLabelStyle = textStyles.sectionLabel;

export function TimelinePanel({
  sourceAssets,
  editingExperience,
  sourceMaterials,
  timelinePlan,
  editingJob,
  lastExportPackage,
  onExportEditingPackage
}: TimelinePanelProps) {
  const videoClipCount =
    timelinePlan.tracks.find((track) => track.type === "video")?.clips.length ?? 0;
  const subtitleClipCount =
    timelinePlan.tracks.find((track) => track.type === "subtitle")?.clips.length ?? 0;
  const totalShots = sourceMaterials.reduce(
    (total, sourceMaterial) => total + sourceMaterial.visualShots.length,
    0
  );
  const totalSentences = sourceMaterials.reduce(
    (total, sourceMaterial) => total + sourceMaterial.transcript.sentences.length,
    0
  );
  const totalBeats = sourceMaterials.reduce((total, sourceMaterial) => total + sourceMaterial.beatsMs.length, 0);
  const totalDrops = sourceMaterials.reduce((total, sourceMaterial) => total + sourceMaterial.dropsMs.length, 0);
  const sourceCaseSummary =
    sourceMaterials.length > 0
      ? sourceMaterials.map((sourceMaterial) => sourceMaterial.sourceCaseId.slice(0, 8)).join(", ")
      : "No material";

  return (
    <section
      style={{
        minHeight: 0,
        overflow: "hidden",
        background: "#101316",
        display: "grid",
        gridTemplateRows: "56px minmax(0, 1fr)"
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
        <div>
          <p style={sectionLabelStyle}>Agent Timeline Preview</p>
        </div>
        <button
          type="button"
          onClick={onExportEditingPackage}
          disabled={sourceAssets.length === 0}
          style={{
            appearance: "none",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "10px",
            background: sourceAssets.length > 0 ? "#e6edf3" : "#20252a",
            color: sourceAssets.length > 0 ? "#101316" : "#77828e",
            padding: "8px 12px",
            ...textStyles.iconButton,
            cursor: sourceAssets.length > 0 ? "pointer" : "default"
          }}
        >
          Export Job
        </button>
      </div>

      <div
        style={{
          minHeight: 0,
          overflow: "auto",
          padding: "16px",
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) 320px",
          gap: "16px",
          background: "#0d1013"
        }}
      >
        <div style={{display: "grid", alignContent: "start", gap: "12px"}}>
          <SummaryCard
            title="Draft Timeline"
            rows={[
              ["Style", editingExperience.styleName],
              ["Target duration", formatDurationMs(timelinePlan.targetDurationMs)],
              ["Video clips", String(videoClipCount)],
              ["Caption clips", String(subtitleClipCount)],
              ["Source materials", `${sourceMaterials.length} cases`]
            ]}
          />
          <div
            style={{
              borderRadius: "14px",
              border: "1px solid rgba(255,255,255,0.06)",
              background: "#12171b",
              padding: "14px",
              display: "grid",
              gap: "10px"
            }}
          >
            <p style={sectionLabelStyle}>Track Preview</p>
            {timelinePlan.tracks.map((track) => (
              <div
                key={track.trackId}
                style={{
                  display: "grid",
                  gridTemplateColumns: "96px minmax(0, 1fr)",
                  gap: "10px",
                  alignItems: "center"
                }}
              >
                <p style={{...textStyles.bodySmall, color: "#9ca7b2"}}>{track.type}</p>
                <div
                  style={{
                    minHeight: "34px",
                    borderRadius: "8px",
                    background: "#080a0c",
                    border: "1px solid rgba(255,255,255,0.06)",
                    display: "flex",
                    gap: "6px",
                    alignItems: "center",
                    padding: "6px",
                    overflow: "hidden"
                  }}
                >
                  {track.clips.length > 0 ? (
                    track.clips.slice(0, 8).map((clip) => (
                      <span
                        key={clip.clipId}
                        style={{
                          minWidth: "48px",
                          maxWidth: "160px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          borderRadius: "7px",
                          background: getTrackColor(track.type),
                          color: "#f3f5f7",
                          padding: "5px 8px",
                          fontSize: "11px"
                        }}
                        title={clip.label}
                      >
                        {clip.label || clip.type}
                      </span>
                    ))
                  ) : (
                    <span style={{...textStyles.bodySmall, color: "#65717c"}}>
                      Waiting for agent plan
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <aside style={{display: "grid", alignContent: "start", gap: "12px"}}>
          <SummaryCard
            title="Source Material"
            rows={[
              ["Cases", sourceCaseSummary],
              ["Shots", String(totalShots)],
              ["Sentences", String(totalSentences)],
              ["Beats", String(totalBeats)],
              ["Drops", String(totalDrops)]
            ]}
          />
          <SummaryCard
            title="HyperFrames Job"
            rows={[
              ["Renderer", editingJob.renderer],
              ["Status", editingJob.status],
              ["Output", editingJob.outputPath],
              ["Format", `${editingJob.renderHints.width}x${editingJob.renderHints.height} mp4`]
            ]}
          />
          <SummaryCard
            title="Export"
            rows={[
              ["Package", lastExportPackage ? "Downloaded" : "Not exported"],
              ["Timeline", lastExportPackage?.timelinePlan.timelineId ?? timelinePlan.timelineId],
              ["Render result", lastExportPackage?.renderResult.status ?? "not_started"]
            ]}
          />
        </aside>
      </div>
    </section>
  );
}

function SummaryCard({
  title,
  rows
}: {
  title: string;
  rows: Array<[string, string]>;
}) {
  return (
    <div
      style={{
        minWidth: 0,
        borderRadius: "14px",
        border: "1px solid rgba(255,255,255,0.06)",
        background: "#12171b",
        padding: "14px"
      }}
    >
      <p style={sectionLabelStyle}>{title}</p>
      <div style={{display: "grid", gap: "8px", marginTop: "12px"}}>
        {rows.map(([label, value]) => (
          <div
            key={label}
            style={{
              display: "grid",
              gridTemplateColumns: "96px minmax(0, 1fr)",
              gap: "10px"
            }}
          >
            <span style={{...textStyles.bodySmall, color: "#7d8792"}}>{label}</span>
            <span
              style={{
                ...textStyles.bodySmall,
                color: "#dbe4ed",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              }}
              title={value}
            >
              {value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function getTrackColor(trackType: string) {
  if (trackType === "video") {
    return "#2f6682";
  }

  if (trackType === "subtitle") {
    return "#755f2a";
  }

  if (trackType === "overlay") {
    return "#674c78";
  }

  return "#54652f";
}

function formatDurationMs(durationMs: number) {
  const seconds = Math.max(0, Math.round(durationMs / 1000));
  const minutes = Math.floor(seconds / 60);
  const restSeconds = seconds % 60;

  return `${minutes}:${restSeconds.toString().padStart(2, "0")}`;
}
