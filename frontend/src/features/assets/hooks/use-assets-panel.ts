"use client";

import {useEffect, useMemo, useRef, useState} from "react";
import {browserAssetPickerGateway} from "../api/browser-asset-picker";
import {localAssetUploadGateway} from "../api/local-asset-upload";
import type {AssetItem, AssetSlot} from "../types/assets";

const browserVideoAccept = "video/*";

function sortAssets(assets: AssetItem[]) {
  return [...assets].sort((left, right) => right.addedAt.localeCompare(left.addedAt));
}

export function useAssetsPanel() {
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [isPicking, setIsPicking] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedReferenceAssetId, setSelectedReferenceAssetId] = useState<string | null>(null);
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

  async function addVideo(slot: AssetSlot) {
    try {
      setError(null);
      setIsPicking(true);
      const pickedAssets = await browserAssetPickerGateway.pickAssets({
        slot,
        accept: browserVideoAccept
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
      if (slot === "REFERENCE") {
        setSelectedReferenceAssetId(firstPickedAsset.assetId);
      }

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

    if (selectedReferenceAssetId === assetId) {
      setSelectedReferenceAssetId(null);
    }

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
    setSelectedReferenceAssetId(null);
    setSelectedSourceAssetId(null);
    setError(null);
    setIsPicking(false);
    setIsRegistering(false);
  }

  const referenceAssets = useMemo(
    () => assets.filter((item) => item.slot === "REFERENCE"),
    [assets]
  );
  const sourceAssets = useMemo(
    () => assets.filter((item) => item.slot === "SOURCE"),
    [assets]
  );
  const selectedReferenceAsset = useMemo(
    () => referenceAssets.find((item) => item.assetId === selectedReferenceAssetId) ?? null,
    [referenceAssets, selectedReferenceAssetId]
  );
  const selectedSourceAsset = useMemo(
    () => sourceAssets.find((item) => item.assetId === selectedSourceAssetId) ?? null,
    [selectedSourceAssetId, sourceAssets]
  );

  return {
    assets,
    referenceAssets,
    sourceAssets,
    selectedReferenceAssetId,
    selectedSourceAssetId,
    selectedReferenceAsset,
    selectedSourceAsset,
    isPicking,
    isRegistering,
    error,
    addReferenceVideo: () => addVideo("REFERENCE"),
    addSourceVideo: () => addVideo("SOURCE"),
    removeAsset,
    resetAssets,
    selectReferenceAsset: setSelectedReferenceAssetId,
    selectSourceAsset: setSelectedSourceAssetId
  };
}
