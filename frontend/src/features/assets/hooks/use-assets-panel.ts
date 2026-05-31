"use client";

import {useEffect, useMemo, useRef, useState} from "react";
import {browserAssetPickerGateway} from "../api/browser-asset-picker";
import {
  deleteWorkspaceAsset,
  listWorkspaceAssets
} from "../api/desktop-workspace-assets";
import {localAssetUploadGateway} from "../api/local-asset-upload";
import type {AssetItem, AssetSlot} from "../types/assets";
import {isDesktopRuntime} from "../../workspace/api/desktop-workspace";

const browserVideoAccept = "video/*";

function sortAssets(assets: AssetItem[]) {
  return [...assets].sort((left, right) => right.addedAt.localeCompare(left.addedAt));
}

export function useAssetsPanel(workspaceId: string | null) {
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [isPicking, setIsPicking] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedReferenceAssetId, setSelectedReferenceAssetId] = useState<string | null>(
    null
  );
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

    const currentWorkspaceId = workspaceId;
    resetAssets();
    let disposed = false;

    async function restoreWorkspaceAssets() {
      if (!isDesktopRuntime()) {
        return;
      }

      try {
        const restoredAssets = await listWorkspaceAssets(currentWorkspaceId);
        if (disposed) {
          restoredAssets.forEach((asset) => {
            if (asset.objectUrl) {
              URL.revokeObjectURL(asset.objectUrl);
            }
          });
          return;
        }

        const sortedAssets = sortAssets(restoredAssets);
        assetsRef.current = sortedAssets;
        setAssets(sortedAssets);
        const restoredReference = sortedAssets.find(
          (item) => item.slot === "REFERENCE"
        );
        const restoredSource = sortedAssets.find((item) => item.slot === "SOURCE");
        setSelectedReferenceAssetId(restoredReference?.assetId ?? null);
        setSelectedSourceAssetId(restoredSource?.assetId ?? null);
      } catch {
        if (!disposed) {
          setError("读取当前工作区素材失败，请稍后重试。");
        }
      }
    }

    void restoreWorkspaceAssets();

    return () => {
      disposed = true;
    };
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

      setAssets((currentAssets) => {
        const nextAssets =
          slot === "REFERENCE"
            ? [
                ...currentAssets.filter((item) => item.slot !== "REFERENCE"),
                ...registeringAssets
              ]
            : [...registeringAssets, ...currentAssets];

        currentAssets
          .filter((item) => slot === "REFERENCE" && item.slot === "REFERENCE")
          .forEach((asset) => {
            if (asset.objectUrl) {
              URL.revokeObjectURL(asset.objectUrl);
            }
          });

        return sortAssets(nextAssets);
      });
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

  async function removeAsset(assetId: string) {
    const assetToRemove = assetsRef.current.find((item) => item.assetId === assetId);
    if (assetToRemove?.workspaceFilePath && isDesktopRuntime()) {
      try {
        await deleteWorkspaceAsset(assetToRemove.workspaceFilePath);
      } catch {
        setError("本地素材删除失败，请稍后重试。");
      }
    }

    setAssets((currentAssets) => {
      const matchedAsset = currentAssets.find((item) => item.assetId === assetId);
      if (matchedAsset?.objectUrl) {
        URL.revokeObjectURL(matchedAsset.objectUrl);
      }

      return currentAssets.filter((item) => item.assetId !== assetId);
    });

    if (selectedSourceAssetId === assetId) {
      setSelectedSourceAssetId(null);
    }
    if (selectedReferenceAssetId === assetId) {
      setSelectedReferenceAssetId(null);
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
    selectedReferenceAsset,
    selectedSourceAssetId,
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
