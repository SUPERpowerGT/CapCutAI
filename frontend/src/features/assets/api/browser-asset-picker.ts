import type {AssetItem, AssetPickRequest, AssetPickerGateway, AssetSlot} from "../types/assets";
import {readVideoPreview} from "../lib/video-preview";

const pickerSafetyTimeoutMs = 15000;

function inferCategory(file: File): AssetItem["category"] {
  if (file.type.startsWith("audio/")) {
    return "AUDIO";
  }

  if (file.type.startsWith("image/")) {
    return "IMAGE";
  }

  return "VIDEO";
}

async function buildAssetItem(
  file: File,
  slot: AssetSlot,
  workspaceId: string
): Promise<AssetItem> {
  const objectUrl = URL.createObjectURL(file);
  const category = inferCategory(file);
  const videoMetadata = category === "VIDEO" ? await readVideoPreview(objectUrl) : {};

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
      input.style.position = "fixed";
      input.style.left = "-9999px";
      input.style.width = "1px";
      input.style.height = "1px";
      input.style.opacity = "0";
      input.style.pointerEvents = "none";

      let settled = false;
      let safetyTimer = 0;

      const cleanup = () => {
        window.clearTimeout(safetyTimer);
        input.remove();
      };

      const finish = (assets: AssetItem[]) => {
        if (settled) {
          return;
        }

        settled = true;
        cleanup();
        resolve(assets);
      };

      input.addEventListener(
        "change",
        async () => {
          const files = Array.from(input.files ?? []);
          const assets = await Promise.all(
            files.map((file) => buildAssetItem(file, request.slot, request.workspaceId))
          );
          finish(assets);
        },
        {once: true}
      );
      input.addEventListener(
        "cancel",
        () => {
          finish([]);
        },
        {once: true}
      );

      document.body.appendChild(input);
      safetyTimer = window.setTimeout(() => {
        if (!settled) {
          finish([]);
        }
      }, pickerSafetyTimeoutMs);
      input.click();
    });
  }
};
