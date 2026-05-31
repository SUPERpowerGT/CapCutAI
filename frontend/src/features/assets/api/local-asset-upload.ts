import type {AssetItem, AssetUploadGateway} from "../types/assets";
import {persistWorkspaceAsset} from "./desktop-workspace-assets";
import {isDesktopRuntime} from "../../workspace/api/desktop-workspace";

function wait(milliseconds: number) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });
}

async function readAssetBytes(asset: AssetItem) {
  if (!asset.objectUrl) {
    throw new Error(`asset ${asset.assetId} has no objectUrl`);
  }

  const response = await fetch(asset.objectUrl);
  const buffer = await response.arrayBuffer();
  return new Uint8Array(buffer);
}

export const localAssetUploadGateway: AssetUploadGateway = {
  async registerAssets(assets: AssetItem[]) {
    await wait(140);

    if (isDesktopRuntime()) {
      return Promise.all(
        assets.map(async (asset) => {
          const bytes = await readAssetBytes(asset);
          const persisted = await persistWorkspaceAsset(asset, bytes);

          return {
            ...asset,
            storageMode: "LOCAL",
            syncStatus: "READY",
            remoteAssetId: `local_${asset.assetId}`,
            workspaceFilePath: persisted.workspaceFilePath,
            workspaceRelativePath: persisted.workspaceRelativePath,
            errorMessage: undefined
          } satisfies AssetItem;
        })
      );
    }

    return assets.map((asset) => ({
      ...asset,
      storageMode: "LOCAL",
      syncStatus: "READY",
      remoteAssetId: `local_${asset.assetId}`,
      workspaceRelativePath:
        asset.slot === "REFERENCE"
          ? `assets/reference/current/${asset.name}`
          : `assets/source/${asset.name}`,
      errorMessage: undefined
    }));
  }
};
