export type AssetCategory = "VIDEO" | "IMAGE" | "AUDIO";

export type AssetItem = {
  assetId: string;
  category: AssetCategory;
  name: string;
};
