"use client";

import {convertFileSrc, invoke} from "@tauri-apps/api/core";
import type {AssetItem} from "../types/assets";

type PersistWorkspaceAssetRequest = {
  assetId: string;
  workspaceId: string;
  slot: AssetItem["slot"];
  fileName: string;
  mimeType: string;
  bytes: number[];
};

type PersistWorkspaceAssetResponse = {
  assetId: string;
  workspaceFilePath: string;
  workspaceRelativePath: string;
};

type WorkspaceAssetDescriptor = {
  assetId: string;
  workspaceId: string;
  slot: AssetItem["slot"];
  name: string;
  mimeType: string;
  sizeBytes: number;
  addedAt: string;
  workspaceFilePath: string;
  workspaceRelativePath: string;
};

export async function persistWorkspaceAsset(
  asset: AssetItem,
  bytes: Uint8Array
): Promise<PersistWorkspaceAssetResponse> {
  return invoke<PersistWorkspaceAssetResponse>("persist_workspace_asset", {
    request: {
      assetId: asset.assetId,
      workspaceId: asset.workspaceId,
      slot: asset.slot,
      fileName: asset.name,
      mimeType: asset.mimeType,
      bytes: Array.from(bytes)
    } satisfies PersistWorkspaceAssetRequest
  });
}

export async function deleteWorkspaceAsset(workspaceFilePath: string) {
  return invoke<void>("delete_workspace_asset", {
    workspaceFilePath
  });
}

export async function listWorkspaceAssets(workspaceId: string): Promise<AssetItem[]> {
  const assets = await invoke<WorkspaceAssetDescriptor[]>("list_workspace_assets", {
    workspaceId
  });

  return assets.map((asset) => ({
    assetId: asset.assetId,
    workspaceId: asset.workspaceId,
    category: "VIDEO",
    slot: asset.slot,
    origin: "DESKTOP",
    storageMode: "LOCAL",
    syncStatus: "READY",
    name: asset.name,
    mimeType: asset.mimeType,
    sizeBytes: asset.sizeBytes,
    addedAt: asset.addedAt,
    objectUrl: convertFileSrc(asset.workspaceFilePath),
    remoteAssetId: `local_${asset.assetId}`,
    workspaceFilePath: asset.workspaceFilePath,
    workspaceRelativePath: asset.workspaceRelativePath
  }));
}
