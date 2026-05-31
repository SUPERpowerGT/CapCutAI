"use client";

import {invoke} from "@tauri-apps/api/core";
import type {AssetItem} from "../types/assets";
import {readVideoPreview} from "../lib/video-preview";

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

export async function openWorkspaceAssetLocation(workspaceFilePath: string) {
  return invoke<void>("open_workspace_asset_location", {
    workspaceFilePath
  });
}

export async function readWorkspaceAssetBytes(workspaceFilePath: string) {
  const bytes = await invoke<number[]>("read_workspace_asset_bytes", {
    workspaceFilePath
  });
  return new Uint8Array(bytes);
}

export async function listWorkspaceAssets(workspaceId: string): Promise<AssetItem[]> {
  const assets = await invoke<WorkspaceAssetDescriptor[]>("list_workspace_assets", {
    workspaceId
  });

  return Promise.all(
    assets.map(async (asset) => {
      const bytes = await readWorkspaceAssetBytes(asset.workspaceFilePath);
      const blob = new Blob([bytes], {type: asset.mimeType || "application/octet-stream"});
      const objectUrl = URL.createObjectURL(blob);
      const videoPreview = await readVideoPreview(objectUrl);

      return {
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
        objectUrl,
        previewImageUrl: videoPreview.previewImageUrl,
        durationSeconds: videoPreview.durationSeconds,
        frameWidth: videoPreview.frameWidth,
        frameHeight: videoPreview.frameHeight,
        remoteAssetId: `local_${asset.assetId}`,
        workspaceFilePath: asset.workspaceFilePath,
        workspaceRelativePath: asset.workspaceRelativePath
      };
    })
  );
}
