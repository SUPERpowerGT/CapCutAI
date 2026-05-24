const sectionLabelStyle = {
  margin: 0,
  fontSize: "11px",
  letterSpacing: "0.12em",
  textTransform: "uppercase" as const,
  color: "#7d8792"
};

const mutedTextStyle = {
  margin: 0,
  color: "#8d96a0",
  fontSize: "12px",
  lineHeight: 1.5
};

export function AssetsSidebar() {
  return (
    <section
      style={{
        minHeight: 0,
        display: "grid",
        gridTemplateRows: "56px 1fr",
        background: "#14171a"
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
        <div>
          <p style={sectionLabelStyle}>Assets</p>
        </div>
      </div>

      <div style={{minHeight: 0, overflow: "auto", padding: "16px"}}>
        <p style={mutedTextStyle}>
          这里是资源模块边界。后续上传、删除、搜索、分类和素材元数据都只往这里接。
        </p>
        <div
          style={{
            marginTop: "16px",
            minHeight: "220px",
            borderRadius: "14px",
            border: "1px dashed rgba(255,255,255,0.10)",
            background: "#111418",
            display: "grid",
            placeItems: "center",
            padding: "20px",
            textAlign: "center"
          }}
        >
          <div>
            <p style={{margin: 0, fontSize: "14px", color: "#d8e0e7"}}>Assets Placeholder</p>
            <p style={{...mutedTextStyle, marginTop: "8px"}}>
              当前只保留左侧资源区边界，不放示例素材内容。
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
