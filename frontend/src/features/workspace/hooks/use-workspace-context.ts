"use client";

import {useEffect, useRef, useState} from "react";

export type WorkspaceContext = {
  workspaceId: string;
  title: string;
  createdAt: string;
};

function formatWorkspaceTitle(workspaceId: string, index: number) {
  const suffix = workspaceId.replace(/^workspace_/, "").slice(0, 6);
  return suffix ? `Workspace ${suffix}` : `Workspace ${index.toString().padStart(2, "0")}`;
}

function buildWorkspaceContext(index: number, workspaceId?: string): WorkspaceContext {
  const resolvedWorkspaceId = workspaceId ?? `workspace_${crypto.randomUUID()}`;
  return {
    workspaceId: resolvedWorkspaceId,
    title: formatWorkspaceTitle(resolvedWorkspaceId, index),
    createdAt: new Date().toISOString()
  };
}

function readWorkspaceIdFromLocation() {
  if (typeof window === "undefined") {
    return null;
  }

  return new URLSearchParams(window.location.search).get("workspaceId");
}

export function useWorkspaceContext() {
  const workspaceIndexRef = useRef(1);
  const [workspaceContext, setWorkspaceContext] = useState<WorkspaceContext>(() => {
    const workspaceIdFromLocation = readWorkspaceIdFromLocation();
    return buildWorkspaceContext(workspaceIndexRef.current, workspaceIdFromLocation ?? undefined);
  });

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const url = new URL(window.location.href);
    if (url.searchParams.get("workspaceId") === workspaceContext.workspaceId) {
      return;
    }

    url.searchParams.set("workspaceId", workspaceContext.workspaceId);
    window.history.replaceState({}, "", url);
  }, [workspaceContext.workspaceId]);

  function createNextWorkspace() {
    workspaceIndexRef.current += 1;
    const nextWorkspace = buildWorkspaceContext(workspaceIndexRef.current);
    setWorkspaceContext(nextWorkspace);
    return nextWorkspace;
  }

  return {
    workspaceContext,
    createNextWorkspace
  };
}
