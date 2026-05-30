import type {CSSProperties} from "react";

export const fontFamilySans =
  '"SF Pro Text", "SF Pro Display", "Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif';

export const fontFamilyMono =
  '"SF Mono", "JetBrains Mono", "Fira Code", "Menlo", "Monaco", monospace';

export const textStyles = {
  sectionLabel: {
    margin: 0,
    fontSize: "11px",
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    color: "#7d8792"
  } satisfies CSSProperties,
  bodySmall: {
    margin: 0,
    fontSize: "12px",
    lineHeight: 1.5,
    color: "#8d96a0"
  } satisfies CSSProperties,
  bodySmallStrong: {
    margin: 0,
    fontSize: "12px",
    fontWeight: 500,
    lineHeight: 1.5,
    color: "#cfd7de"
  } satisfies CSSProperties,
  body: {
    margin: 0,
    fontSize: "14px",
    lineHeight: 1.6,
    color: "#d8e0e7"
  } satisfies CSSProperties,
  titleSmall: {
    margin: 0,
    fontSize: "13px",
    fontWeight: 600,
    lineHeight: 1.4,
    color: "#e9edf0"
  } satisfies CSSProperties,
  titleMedium: {
    margin: 0,
    fontSize: "16px",
    fontWeight: 600,
    lineHeight: 1.4,
    color: "#eef3f7"
  } satisfies CSSProperties,
  display: {
    margin: 0,
    fontSize: "17px",
    fontWeight: 600,
    lineHeight: 1.5,
    color: "#d8e0e7"
  } satisfies CSSProperties,
  windowTitle: {
    margin: 0,
    fontSize: "13px",
    fontWeight: 600,
    lineHeight: 1.4,
    color: "#e9edf0"
  } satisfies CSSProperties,
  button: {
    fontSize: "12px",
    fontWeight: 600,
    lineHeight: 1.2
  } satisfies CSSProperties,
  iconButton: {
    fontSize: "11px",
    fontWeight: 600,
    lineHeight: 1
  } satisfies CSSProperties
};
