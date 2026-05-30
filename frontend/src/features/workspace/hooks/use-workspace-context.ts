"use client";

import {useEffect, useRef, useState} from "react";
import {
  createDesktopWorkspace,
  ensureDesktopWorkspace,
  isDesktopRuntime
} from "../api/desktop-workspace";

export type WorkspaceContext = {
  workspaceId: string;
  title: string;
  createdAt: string;
  folderPath?: string;
};

const PENDING_WORKSPACE_ID = "workspace_pending";

function formatWorkspaceTitle(workspaceId: string, index: number) {
  if (workspaceId === PENDING_WORKSPACE_ID) {
    return "Workspace";
  }

  const suffix = workspaceId.replace(/^workspace_/, "").slice(0, 6);
  return suffix ? `Workspace ${suffix}` : `Workspace ${index.toString().padStart(2, "0")}`;
}

function buildWorkspaceContext(index: number, workspaceId?: string): WorkspaceContext {
  const resolvedWorkspaceId = workspaceId ?? PENDING_WORKSPACE_ID;
  return {
    workspaceId: resolvedWorkspaceId,
    title: formatWorkspaceTitle(resolvedWorkspaceId, index),
    createdAt: new Date().toISOString()
  };
}

function fromDesktopDescriptor(descriptor: {
  workspaceId: string;
  title: string;
  createdAt: string;
  folderPath: string;
}): WorkspaceContext {
  return {
    workspaceId: descriptor.workspaceId,
    title: descriptor.title,
    createdAt: descriptor.createdAt,
    folderPath: descriptor.folderPath
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
  const [isReady, setIsReady] = useState(false);
  const [workspaceContext, setWorkspaceContext] = useState<WorkspaceContext>(() =>
    buildWorkspaceContext(workspaceIndexRef.current)
  );

  useEffect(() => {
    let disposed = false;

    async function hydrateWorkspace() {
      const workspaceIdFromLocation = readWorkspaceIdFromLocation();

      if (isDesktopRuntime()) {
        try {
          const descriptor = await ensureDesktopWorkspace(workspaceIdFromLocation ?? undefined);
          if (!disposed) {
            setWorkspaceContext(fromDesktopDescriptor(descriptor));
            setIsReady(true);
          }
          return;
        } catch (error) {
          console.error("Failed to resolve desktop workspace", error);
        }
      }

      const resolvedWorkspaceId = workspaceIdFromLocation ?? `workspace_${crypto.randomUUID()}`;
      if (!disposed) {
        setWorkspaceContext((current) => {
          if (current.workspaceId === resolvedWorkspaceId) {
            return current;
          }

          return buildWorkspaceContext(workspaceIndexRef.current, resolvedWorkspaceId);
        });
        setIsReady(true);
      }
    }

    void hydrateWorkspace();

    return () => {
      disposed = true;
    };
  }, []);

  useEffect(() => {
    if (!isReady || typeof window === "undefined") {
      return;
    }

    const url = new URL(window.location.href);
    if (url.searchParams.get("workspaceId") === workspaceContext.workspaceId) {
      return;
    }

    url.searchParams.set("workspaceId", workspaceContext.workspaceId);
    window.history.replaceState({}, "", url);
  }, [isReady, workspaceContext.workspaceId]);

  async function createNextWorkspace() {
    workspaceIndexRef.current += 1;
    const nextWorkspace = isDesktopRuntime()
      ? fromDesktopDescriptor(await createDesktopWorkspace())
      : buildWorkspaceContext(workspaceIndexRef.current, `workspace_${crypto.randomUUID()}`);
    setWorkspaceContext(nextWorkspace);
    setIsReady(true);
    return nextWorkspace;
  }

  return {
    workspaceContext,
    isReady,
    createNextWorkspace
  };
}
