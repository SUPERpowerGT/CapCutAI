import {textStyles} from "../../../shared/design/typography";

type PreviewViewportProps = {
  title: string;
  subtitle?: string;
  previewSource?: {
    objectUrl?: string;
    name: string;
    mimeType: string;
  } | null;
};

const sectionLabelStyle = textStyles.sectionLabel;

export function PreviewViewport({title, subtitle, previewSource}: PreviewViewportProps) {
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
    </section>
  );
}
