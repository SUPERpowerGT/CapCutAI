const sectionLabelStyle = {
  margin: 0,
  fontSize: "11px",
  letterSpacing: "0.12em",
  textTransform: "uppercase" as const,
  color: "#7d8792"
};

export function TimelinePanel() {
  return (
    <section
      style={{
        minHeight: 0,
        overflow: "auto",
        padding: "16px",
        background: "#101316"
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "12px"
        }}
      >
        <p style={sectionLabelStyle}>Timeline</p>
        <span style={{fontSize: "12px", color: "#86909a"}}>HyperFrames 接这里</span>
      </div>

      <div
        style={{
          marginTop: "14px",
          borderRadius: "16px",
          border: "1px solid rgba(255,255,255,0.06)",
          background: "#0d1013",
          padding: "16px"
        }}
      >
        <div
          style={{
            minHeight: "180px",
            borderRadius: "14px",
            border: "1px dashed rgba(255,255,255,0.10)",
            background: "#14181c",
            display: "grid",
            placeItems: "center",
            padding: "20px",
            textAlign: "center"
          }}
        >
          <div>
            <p style={{margin: 0, fontSize: "14px", color: "#d8e0e7"}}>Timeline Placeholder</p>
            <p
              style={{
                margin: "8px 0 0",
                color: "#8d96a0",
                fontSize: "13px",
                lineHeight: 1.6
              }}
            >
              当前只保留时间轴边界，后续由 HyperFrames 或真实时间轴组件接入。
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
