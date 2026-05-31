"use client";

import {useEffect, useMemo, useRef, useState} from "react";
import {browserAssetPickerGateway} from "../api/browser-asset-picker";
import {localAssetUploadGateway} from "../api/local-asset-upload";
import type {AssetItem, AssetSlot} from "../types/assets";

const browserVideoAccept = "video/*";

function sortAssets(assets: AssetItem[]) {
  return [...assets].sort((left, right) => right.addedAt.localeCompare(left.addedAt));
}

export function useAssetsPanel(workspaceId: string | null) {
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [isPicking, setIsPicking] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSourceAssetId, setSelectedSourceAssetId] = useState<string | null>(null);
  const assetsRef = useRef<AssetItem[]>([]);

  useEffect(() => {
    assetsRef.current = assets;
  }, [assets]);

  useEffect(() => {
    return () => {
      assetsRef.current.forEach((asset) => {
        if (asset.objectUrl) {
          URL.revokeObjectURL(asset.objectUrl);
        }
      });
    };
  }, []);

  useEffect(() => {
    if (!workspaceId) {
      resetAssets();
      return;
    }

    resetAssets();
  }, [workspaceId]);

  async function addVideo(slot: AssetSlot) {
    if (!workspaceId) {
      setError("当前工作区还没准备好，请稍后再试。");
      return;
    }

    try {
      setError(null);
      setIsPicking(true);
      const pickedAssets = await browserAssetPickerGateway.pickAssets({
        workspaceId,
        slot,
        accept: browserVideoAccept,
        multiple: slot === "SOURCE"
      });

      if (pickedAssets.length === 0) {
        return;
      }

      const registeringAssets = pickedAssets.map((asset) => ({
        ...asset,
        syncStatus: "REGISTERING" as const
      }));

      setAssets((currentAssets) => sortAssets([...registeringAssets, ...currentAssets]));
      const [firstPickedAsset] = pickedAssets;
      if (slot === "SOURCE") {
        setSelectedSourceAssetId(firstPickedAsset.assetId);
      }

      setIsRegistering(true);
      const registeredAssets = await localAssetUploadGateway.registerAssets(registeringAssets);
      setAssets((currentAssets) =>
        sortAssets(
          currentAssets.map((asset) => {
            const registeredAsset = registeredAssets.find(
              (item) => item.assetId === asset.assetId
            );

            return registeredAsset ?? asset;
          })
        )
      );
    } catch {
      setError("当前文件选择失败，请重试。");
    } finally {
      setIsPicking(false);
      setIsRegistering(false);
    }
  }

  function removeAsset(assetId: string) {
    setAssets((currentAssets) => {
      const assetToRemove = currentAssets.find((item) => item.assetId === assetId);
      if (assetToRemove?.objectUrl) {
        URL.revokeObjectURL(assetToRemove.objectUrl);
      }

      return currentAssets.filter((item) => item.assetId !== assetId);
    });

    if (selectedSourceAssetId === assetId) {
      setSelectedSourceAssetId(null);
    }
  }

  function resetAssets() {
    assetsRef.current.forEach((asset) => {
      if (asset.objectUrl) {
        URL.revokeObjectURL(asset.objectUrl);
      }
    });

    assetsRef.current = [];
    setAssets([]);
    setSelectedSourceAssetId(null);
    setError(null);
    setIsPicking(false);
    setIsRegistering(false);
  }

  const sourceAssets = useMemo(
    () => assets.filter((item) => item.slot === "SOURCE"),
    [assets]
  );
  const selectedSourceAsset = useMemo(
    () => sourceAssets.find((item) => item.assetId === selectedSourceAssetId) ?? null,
    [selectedSourceAssetId, sourceAssets]
  );

  return {
    assets,
    sourceAssets,
    selectedSourceAssetId,
    selectedSourceAsset,
    isPicking,
    isRegistering,
    error,
    addSourceVideo: () => addVideo("SOURCE"),
    removeAsset,
    resetAssets,
    selectSourceAsset: setSelectedSourceAssetId
  };
}
