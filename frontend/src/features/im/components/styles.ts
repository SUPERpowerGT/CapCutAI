import type {CSSProperties} from "react";
import type {Message} from "../types/contracts";

export const appShellStyle: CSSProperties = {
  minHeight: "100vh",
  height: "100vh",
  padding: "12px",
  background: "#0f1113"
};

export const frameStyle: CSSProperties = {
  height: "calc(100vh - 24px)",
  display: "grid",
  gridTemplateRows: "56px 1fr",
  borderRadius: "20px",
  overflow: "hidden",
  border: "1px solid rgba(255,255,255,0.08)",
  background: "#15181b",
  boxShadow: "0 24px 64px rgba(0,0,0,0.35)"
};

export const sectionLabelStyle: CSSProperties = {
  margin: 0,
  fontSize: "11px",
  letterSpacing: "0.12em",
  textTransform: "uppercase",
  color: "#7d8792"
};

export const mutedTextStyle: CSSProperties = {
  margin: 0,
  color: "#8d96a0",
  fontSize: "12px",
  lineHeight: 1.5
};

export const buttonStyle: CSSProperties = {
  border: "1px solid rgba(255,255,255,0.08)",
  background: "#f3f5f7",
  color: "#111315",
  borderRadius: "10px",
  padding: "10px 14px",
  fontSize: "12px",
  fontWeight: 600,
  cursor: "pointer"
};

export const roleStyleMap: Record<Message["role"], CSSProperties> = {
  USER: {
    background: "#20262c",
    border: "1px solid rgba(255,255,255,0.08)",
    justifySelf: "end"
  },
  ASSISTANT: {
    background: "transparent",
    border: "none",
    justifySelf: "start"
  },
  SYSTEM: {
    background: "#13171b",
    border: "1px dashed rgba(255,255,255,0.08)",
    justifySelf: "center"
  }
};
