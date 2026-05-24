type PreviewViewportProps = {
  title: string;
};

const sectionLabelStyle = {
  margin: 0,
  fontSize: "11px",
  letterSpacing: "0.12em",
  textTransform: "uppercase" as const,
  color: "#7d8792"
};

export function PreviewViewport({title}: PreviewViewportProps) {
  return (
    <section
      style={{
        minHeight: 0,
        overflow: "hidden",
        padding: "16px",
        background: "#121518",
        borderBottom: "1px solid rgba(255,255,255,0.06)"
      }}
    >
      <p style={sectionLabelStyle}>Preview</p>
      <div
        style={{
          marginTop: "12px",
          height: "calc(100% - 31px)",
          borderRadius: "18px",
          border: "1px solid rgba(255,255,255,0.06)",
          background:
            "radial-gradient(circle at top right, rgba(255,153,102,0.18), transparent 24%), #0d1013",
          padding: "18px",
          display: "grid",
          placeItems: "center",
          overflow: "hidden"
        }}
      >
        <div
          style={{
            aspectRatio: "16 / 9",
            width: "100%",
            maxWidth: "100%",
            maxHeight: "100%",
            borderRadius: "16px",
            overflow: "hidden",
            background: "linear-gradient(135deg, rgba(34,40,47,1) 0%, rgba(16,19,23,1) 100%)",
            border: "1px solid rgba(255,255,255,0.06)",
            display: "grid",
            placeItems: "center",
            padding: "20px"
          }}
        >
          <div style={{textAlign: "center", maxWidth: "520px"}}>
            <p style={{...sectionLabelStyle, color: "#98a5b2"}}>Live Preview</p>
            <h2 style={{margin: "8px 0 0", fontSize: "28px", lineHeight: 1.2}}>{title}</h2>
            <p
              style={{
                margin: "12px 0 0",
                color: "#d8e0e7",
                fontSize: "16px",
                lineHeight: 1.6
              }}
            >
              Preview Placeholder
            </p>
            <p
              style={{
                margin: "8px 0 0",
                color: "#8d96a0",
                fontSize: "13px",
                lineHeight: 1.6
              }}
            >
              当前中间上方只保留预览区边界，后续由 HyperFrames 或真正预览播放器接入。
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
