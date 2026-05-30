import {PreviewViewport} from "./PreviewViewport";
import {TimelinePanel} from "./TimelinePanel";

type EditorSurfaceProps = {
  title: string;
  subtitle?: string;
  previewSource?: {
    objectUrl?: string;
    name: string;
    mimeType: string;
  } | null;
  previewHeightPercent: number;
  isBottomPaneCollapsed?: boolean;
  onResizeStart: () => void;
};

export function EditorSurface({
  title,
  subtitle,
  previewSource,
  previewHeightPercent,
  isBottomPaneCollapsed = false,
  onResizeStart
}: EditorSurfaceProps) {
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
      <PreviewViewport title={title} subtitle={subtitle} previewSource={previewSource} />
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
          <TimelinePanel />
        </>
      ) : null}
    </section>
  );
}
