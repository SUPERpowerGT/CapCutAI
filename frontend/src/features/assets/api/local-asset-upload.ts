import type {AssetItem, AssetUploadGateway} from "../types/assets";

function wait(milliseconds: number) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });
}

export const localAssetUploadGateway: AssetUploadGateway = {
  async registerAssets(assets: AssetItem[]) {
    await wait(140);

    return assets.map((asset) => ({
      ...asset,
      storageMode: "LOCAL",
      syncStatus: "READY",
      remoteAssetId: `local_${asset.assetId}`,
      errorMessage: undefined
    }));
  }
};
