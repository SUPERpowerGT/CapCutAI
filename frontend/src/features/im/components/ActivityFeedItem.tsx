import type {AgentActivityItem} from "../types/contracts";
import {textStyles} from "../../../shared/design/typography";

type ActivityFeedItemProps = {
  activity: AgentActivityItem;
};

const stateColorMap: Record<AgentActivityItem["state"], string> = {
  IDLE: "#8f99a4",
  THINKING: "#ffd27d",
  STREAMING: "#83b0ff",
  COMPLETED: "#93d6a3",
  FAILED: "#ffb2b2"
};

const stateLabelMap: Record<AgentActivityItem["state"], string> = {
  IDLE: "Idle",
  THINKING: "Working",
  STREAMING: "Responding",
  COMPLETED: "Ready",
  FAILED: "Failed"
};

export function ActivityFeedItem({activity}: ActivityFeedItemProps) {
  const showDots = activity.state === "THINKING" || activity.state === "STREAMING";
  const detailLines = activity.detail.split("\n").filter(Boolean);

  return (
    <div
      className="agent-activity"
      style={{
        ...textStyles.bodySmallStrong,
        color: activity.state === "FAILED" ? "#ffd4d4" : "#c8d0d8"
      }}
    >
      {showDots ? (
        <div className="agent-activity-dots" aria-hidden="true">
          <span className="agent-activity-dot" />
          <span className="agent-activity-dot" />
          <span className="agent-activity-dot" />
        </div>
      ) : null}

      <div
        className="agent-activity-caption"
        style={{
          ...textStyles.bodySmall,
          color: activity.state === "FAILED" ? "#ffd4d4" : "#8f99a4"
        }}
      >
        {detailLines.map((line, index) => (
          <div
            key={`${activity.id}-detail-${index}`}
            className={index > 0 ? "agent-activity-progress-line" : undefined}
          >
            {line}
          </div>
        ))}
        <div
          className="agent-activity-label"
          style={{
            ...textStyles.button,
            color: stateColorMap[activity.state]
          }}
        >
          {activity.kind === "STATUS"
            ? stateLabelMap[activity.state]
            : `${activity.kind}${activity.source ? ` · ${activity.source}` : ""}`}
        </div>
      </div>
    </div>
  );
}
