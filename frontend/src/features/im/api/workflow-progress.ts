"use client";

import {isDesktopRuntime} from "../../workspace/api/desktop-workspace";

export type WorkspaceAnalysisProgress = {
  workspaceId: string;
  stage: string;
  title: string;
  detail: string;
  completed: boolean;
  templatePath: string;
  intermediateDir: string;
  step1AudioExists: boolean;
  step2TranscriptExists: boolean;
  step3VisualExists: boolean;
  elasticTemplateExists: boolean;
};

export async function inspectWorkspaceAnalysisProgress(workspaceId: string) {
  if (!isDesktopRuntime()) {
    return null;
  }

  const core = await import("@tauri-apps/api/core");
  return core.invoke<WorkspaceAnalysisProgress>("inspect_workspace_analysis_progress", {
    workspaceId
  });
}
