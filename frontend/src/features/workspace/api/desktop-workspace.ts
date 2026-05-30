"use client";

export type DesktopWorkspaceDescriptor = {
  workspaceId: string;
  title: string;
  createdAt: string;
  lastOpenedAt: string;
  folderPath: string;
};

export function isDesktopRuntime() {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

async function invokeWorkspaceCommand<T>(command: string, args?: Record<string, unknown>) {
  const core = await import("@tauri-apps/api/core");
  return core.invoke<T>(command, args);
}

export function ensureDesktopWorkspace(workspaceId?: string | null) {
  return invokeWorkspaceCommand<DesktopWorkspaceDescriptor>("ensure_workspace", {
    workspaceId: workspaceId ?? null
  });
}

export function createDesktopWorkspace() {
  return invokeWorkspaceCommand<DesktopWorkspaceDescriptor>("create_workspace");
}
