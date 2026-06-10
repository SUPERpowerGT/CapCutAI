"use client";

import {invoke} from "@tauri-apps/api/core";

export type LocalRuntimeCheckItem = {
  name: string;
  available: boolean;
  detail: string;
};

export type LocalRuntimeInspection = {
  ready: boolean;
  summary: string;
  checks: LocalRuntimeCheckItem[];
};

export async function inspectLocalRuntime(): Promise<LocalRuntimeInspection> {
  return invoke<LocalRuntimeInspection>("inspect_local_runtime");
}
