type AgentStatusBarProps = {
  status: string;
  summary: string;
};

const statusStyleMap: Record<string, {label: string; color: string; background: string}> = {
  IDLE: {
    label: "Idle",
    color: "#aeb8c1",
    background: "rgba(255,255,255,0.06)"
  },
  THINKING: {
    label: "Thinking",
    color: "#ffd27d",
    background: "rgba(255,210,125,0.12)"
  },
  STREAMING: {
    label: "Responding",
    color: "#83b0ff",
    background: "rgba(131,176,255,0.14)"
  },
  COMPLETED: {
    label: "Ready",
    color: "#93d6a3",
    background: "rgba(147,214,163,0.14)"
  },
  FAILED: {
    label: "Failed",
    color: "#ff9b9b",
    background: "rgba(255,155,155,0.14)"
  }
};

export function AgentStatusBar({status, summary}: AgentStatusBarProps) {
  const normalizedStatus = status.toUpperCase();
  const appearance = statusStyleMap[normalizedStatus] ?? statusStyleMap.IDLE;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px",
        padding: "10px 12px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        background: "#15191d"
      }}
    >
      <div style={{minWidth: 0}}>
        <div
          style={{
            fontSize: "11px",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: "#77818b",
            marginBottom: "4px"
          }}
        >
          Current Task
        </div>
        <div
          style={{
            fontSize: "13px",
            lineHeight: 1.4,
            color: "#d9e0e6",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis"
          }}
        >
          {summary}
        </div>
      </div>
      <div
        style={{
          flex: "0 0 auto",
          borderRadius: "999px",
          padding: "6px 10px",
          fontSize: "11px",
          fontWeight: 600,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: appearance.color,
          background: appearance.background
        }}
      >
        {appearance.label}
      </div>
    </div>
  );
}
