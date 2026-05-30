import {textStyles} from "../../../shared/design/typography";

const sectionLabelStyle = textStyles.sectionLabel;

export function TimelinePanel() {
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
          justifyContent: "flex-start",
          padding: "0 16px",
          borderBottom: "1px solid rgba(255,255,255,0.06)"
        }}
      >
        <p style={sectionLabelStyle}>Timeline</p>
      </div>

      <div
        style={{
          minHeight: 0,
          display: "grid",
          placeItems: "center",
          padding: "16px",
          textAlign: "center",
          background: "#0d1013"
        }}
      >
          <div>
            <p style={{...sectionLabelStyle, color: "#98a5b2"}}>Timeline</p>
            <p
              style={{
                ...textStyles.display,
                margin: "16px 0 0"
              }}
            >
              时间轴会在这里展开。
            </p>
          </div>
        </div>
    </section>
  );
}
