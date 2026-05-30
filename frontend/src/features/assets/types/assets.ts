export type AssetCategory = "VIDEO" | "IMAGE" | "AUDIO";

export type AssetSlot = "REFERENCE" | "SOURCE" | "SUPPORTING";

export type AssetOrigin = "BROWSER" | "DESKTOP";
export type AssetStorageMode = "LOCAL" | "CLOUD";
export type AssetSyncStatus = "PICKED" | "REGISTERING" | "READY" | "FAILED";

export type AssetItem = {
  assetId: string;
  category: AssetCategory;
  slot: AssetSlot;
  origin: AssetOrigin;
  storageMode: AssetStorageMode;
  syncStatus: AssetSyncStatus;
  name: string;
  mimeType: string;
  sizeBytes: number;
  addedAt: string;
  durationSeconds?: number;
  frameWidth?: number;
  frameHeight?: number;
  objectUrl?: string;
  remoteAssetId?: string;
  errorMessage?: string;
};

export type AssetPickRequest = {
  slot: AssetSlot;
  accept: string;
  multiple?: boolean;
};

export type AssetPickerGateway = {
  pickAssets(request: AssetPickRequest): Promise<AssetItem[]>;
};

export type AssetUploadGateway = {
  registerAssets(assets: AssetItem[]): Promise<AssetItem[]>;
};
