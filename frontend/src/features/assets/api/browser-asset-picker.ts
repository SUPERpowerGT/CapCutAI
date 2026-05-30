import type {AssetItem, AssetPickRequest, AssetPickerGateway, AssetSlot} from "../types/assets";

function inferCategory(file: File): AssetItem["category"] {
  if (file.type.startsWith("audio/")) {
    return "AUDIO";
  }

  if (file.type.startsWith("image/")) {
    return "IMAGE";
  }

  return "VIDEO";
}

async function readVideoMetadata(objectUrl: string) {
  return new Promise<{
    durationSeconds?: number;
    frameWidth?: number;
    frameHeight?: number;
  }>((resolve) => {
    const video = document.createElement("video");
    video.preload = "metadata";
    video.src = objectUrl;

    const finish = () => {
      resolve({
        durationSeconds:
          Number.isFinite(video.duration) && video.duration > 0 ? video.duration : undefined,
        frameWidth: video.videoWidth || undefined,
        frameHeight: video.videoHeight || undefined
      });
      video.removeAttribute("src");
      video.load();
    };

    video.onloadedmetadata = finish;
    video.onerror = () => resolve({});
  });
}

async function buildAssetItem(
  file: File,
  slot: AssetSlot,
  workspaceId: string
): Promise<AssetItem> {
  const objectUrl = URL.createObjectURL(file);
  const category = inferCategory(file);
  const videoMetadata =
    category === "VIDEO" ? await readVideoMetadata(objectUrl) : {};

  return {
    assetId: `asset_${crypto.randomUUID()}`,
    workspaceId,
    category,
    slot,
    origin: "BROWSER",
    storageMode: "LOCAL",
    syncStatus: "PICKED",
    name: file.name,
    mimeType: file.type || "application/octet-stream",
    sizeBytes: file.size,
    addedAt: new Date().toISOString(),
    objectUrl,
    ...videoMetadata
  };
}

export const browserAssetPickerGateway: AssetPickerGateway = {
  pickAssets(request: AssetPickRequest) {
    return new Promise((resolve) => {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = request.accept;
      input.multiple = request.multiple ?? false;
      input.style.display = "none";

      input.addEventListener(
        "change",
        async () => {
          const files = Array.from(input.files ?? []);
          const assets = await Promise.all(
            files.map((file) => buildAssetItem(file, request.slot, request.workspaceId))
          );
          resolve(assets);
          input.remove();
        },
        {once: true}
      );

      document.body.appendChild(input);
      input.click();
    });
  }
};
