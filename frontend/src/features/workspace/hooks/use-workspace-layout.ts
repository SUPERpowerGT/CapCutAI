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
  const dragModeRef = useRef<DragMode>(null);

  useEffect(() => {
    const handlePointerMove = (event: MouseEvent) => {
      const container = containerRef.current;
      if (!container || !dragModeRef.current) return;

      const rect = container.getBoundingClientRect();
      const relativeX = ((event.clientX - rect.left) / rect.width) * 100;
      const relativeY = ((event.clientY - rect.top) / rect.height) * 100;

      if (dragModeRef.current === "left") {
        setLeftPaneWidth(clamp(relativeX, 16, 32));
      }

      if (dragModeRef.current === "right") {
        const width = 100 - relativeX;
        setRightPaneWidth(clamp(width, 24, 38));
      }

      if (dragModeRef.current === "horizontal") {
        setPreviewHeight(clamp(relativeY, 38, 72));
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
    startLeftResize: () => {
      dragModeRef.current = "left";
    },
    startRightResize: () => {
      dragModeRef.current = "right";
    },
    startHorizontalResize: () => {
      dragModeRef.current = "horizontal";
    }
  };
}
