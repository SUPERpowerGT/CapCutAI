"use client";

import {useEffect, useRef, useState} from "react";

type DragMode = "left" | "right" | "horizontal" | null;

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

export function useWorkspaceLayout() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [leftPaneWidth, setLeftPaneWidth] = useState(21);
  const [rightPaneWidth, setRightPaneWidth] = useState(29);
  const [previewHeight, setPreviewHeight] = useState(58);
  const [isLeftPaneCollapsed, setIsLeftPaneCollapsed] = useState(false);
  const [isRightPaneCollapsed, setIsRightPaneCollapsed] = useState(false);
  const [isBottomPaneCollapsed, setIsBottomPaneCollapsed] = useState(false);
  const dragModeRef = useRef<DragMode>(null);
  const lastLeftPaneWidthRef = useRef(21);
  const lastRightPaneWidthRef = useRef(29);
  const lastPreviewHeightRef = useRef(58);

  useEffect(() => {
    const handlePointerMove = (event: MouseEvent) => {
      const container = containerRef.current;
      if (!container || !dragModeRef.current) return;

      const rect = container.getBoundingClientRect();
      const relativeX = ((event.clientX - rect.left) / rect.width) * 100;
      const relativeY = ((event.clientY - rect.top) / rect.height) * 100;

      if (dragModeRef.current === "left") {
        const next = clamp(relativeX, 16, 32);
        lastLeftPaneWidthRef.current = next;
        setLeftPaneWidth(next);
      }

      if (dragModeRef.current === "right") {
        const width = 100 - relativeX;
        const next = clamp(width, 24, 38);
        lastRightPaneWidthRef.current = next;
        setRightPaneWidth(next);
      }

      if (dragModeRef.current === "horizontal") {
        const next = clamp(relativeY, 38, 72);
        lastPreviewHeightRef.current = next;
        setPreviewHeight(next);
      }
    };

    const handlePointerUp = () => {
      dragModeRef.current = null;
    };

    window.addEventListener("mousemove", handlePointerMove);
    window.addEventListener("mouseup", handlePointerUp);

    return () => {
      window.removeEventListener("mousemove", handlePointerMove);
      window.removeEventListener("mouseup", handlePointerUp);
    };
  }, []);

  return {
    containerRef,
    leftPaneWidth,
    rightPaneWidth,
    previewHeight,
    isLeftPaneCollapsed,
    isRightPaneCollapsed,
    isBottomPaneCollapsed,
    startLeftResize: () => {
      dragModeRef.current = "left";
    },
    startRightResize: () => {
      dragModeRef.current = "right";
    },
    startHorizontalResize: () => {
      dragModeRef.current = "horizontal";
    },
    toggleLeftPane: () => {
      setIsLeftPaneCollapsed((current) => {
        const next = !current;
        if (!next) {
          setLeftPaneWidth(lastLeftPaneWidthRef.current);
        } else {
          lastLeftPaneWidthRef.current = leftPaneWidth;
        }
        return next;
      });
    },
    toggleRightPane: () => {
      setIsRightPaneCollapsed((current) => {
        const next = !current;
        if (!next) {
          setRightPaneWidth(lastRightPaneWidthRef.current);
        } else {
          lastRightPaneWidthRef.current = rightPaneWidth;
        }
        return next;
      });
    },
    toggleBottomPane: () => {
      setIsBottomPaneCollapsed((current) => {
        const next = !current;
        if (!next) {
          setPreviewHeight(lastPreviewHeightRef.current);
        } else {
          lastPreviewHeightRef.current = previewHeight;
          setPreviewHeight(100);
        }
        return next;
      });
    }
  };
}
