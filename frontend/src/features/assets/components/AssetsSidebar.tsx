"use client";

import type {AssetItem} from "../types/assets";
import {textStyles} from "../../../shared/design/typography";

const sectionLabelStyle = textStyles.sectionLabel;
const mutedTextStyle = textStyles.bodySmall;

type AssetsSidebarProps = {
  workspaceTitle: string;
  referenceAssets: AssetItem[];
  sourceAssets: AssetItem[];
  selectedReferenceAssetId: string | null;
  selectedSourceAssetId: string | null;
  isPicking: boolean;
  isRegistering: boolean;
  error: string | null;
  onAddReferenceVideo: () => void;
  onAddSourceVideo: () => void;
  onRemoveAsset: (assetId: string) => void;
  onSelectReferenceAsset: (assetId: string) => void;
  onSelectSourceAsset: (assetId: string) => void;
};

export function AssetsSidebar({
  workspaceTitle,
  referenceAssets,
  sourceAssets,
  selectedReferenceAssetId,
  selectedSourceAssetId,
  isPicking,
  isRegistering,
  error,
  onAddSourceVideo,
  onRemoveAsset,
  onSelectSourceAsset
}: AssetsSidebarProps) {
  const selectedSourceAsset =
    sourceAssets.find((item) => item.assetId === selectedSourceAssetId) ?? null;
  const fallbackReferenceAsset =
    referenceAssets.find((item) => item.assetId === selectedReferenceAssetId) ?? null;
  const primaryAsset = selectedSourceAsset ?? fallbackReferenceAsset;

  return (
    <section
      style={{
        minHeight: 0,
        display: "grid",
        gridTemplateRows: "56px 1fr",
        background: "#14171a"
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "0 16px",
          borderBottom: "1px solid rgba(255,255,255,0.06)"
        }}
      >
        <p style={sectionLabelStyle}>Assets</p>
      </div>

      <div
        style={{
          minHeight: 0,
          overflow: "auto",
          padding: "16px",
          display: "grid",
          alignContent: "start",
          gap: "16px"
        }}
      >
        <div
          style={{
            display: "grid",
            gap: "4px"
          }}
        >
          <p style={sectionLabelStyle}>Workspace</p>
          <p
            style={{
              ...textStyles.titleSmall,
              color: "#d7dfe6",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap"
            }}
            title={workspaceTitle}
          >
            {workspaceTitle}
          </p>
        </div>

        <UploadPanel
          disabled={isPicking || isRegistering}
          isBusy={isPicking || isRegistering}
          onClick={onAddSourceVideo}
        />

        {error ? <p style={{...mutedTextStyle, color: "#f2a3a3"}}>{error}</p> : null}

        <section style={{display: "grid", gap: "10px"}}>
          <p style={sectionLabelStyle}>Current Video</p>
          {primaryAsset ? (
            <AssetCard
              asset={primaryAsset}
              isActive
              onSelect={() => onSelectSourceAsset(primaryAsset.assetId)}
              onRemove={() => onRemoveAsset(primaryAsset.assetId)}
            />
          ) : (
            <EmptyState />
          )}
        </section>
      </div>
    </section>
  );
}

function UploadPanel({
  disabled,
  isBusy,
  onClick
}: {
  disabled: boolean;
  isBusy: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      style={{
        appearance: "none",
        width: "100%",
        minHeight: "180px",
        borderRadius: "16px",
        border: "1px dashed rgba(255,255,255,0.12)",
        background: "linear-gradient(180deg, #171a1e 0%, #111418 100%)",
        padding: "20px 18px",
        display: "grid",
        placeItems: "center",
        textAlign: "center",
        cursor: disabled ? "default" : "pointer"
      }}
    >
      <div style={{display: "grid", gap: "14px", justifyItems: "center", maxWidth: "100%"}}>
        <div
          style={{
            width: "42px",
            height: "42px",
            borderRadius: "12px",
            display: "grid",
            placeItems: "center",
            background: "rgba(121,192,255,0.10)",
            color: "#78b7ff",
            fontSize: "18px",
            fontWeight: 700
          }}
        >
          ↑
        </div>
        <div style={{display: "grid", gap: "6px"}}>
          <p
            style={{
              ...textStyles.titleMedium,
              fontSize: "18px",
              color: disabled ? "#8a949f" : "#dfe7ee"
            }}
          >
            {isBusy ? "Selecting..." : "上传视频"}
          </p>
          <p style={{...mutedTextStyle, maxWidth: "240px"}}>
            选择一个本地视频作为当前工作素材。后续分析、生成和修订都围绕这条素材展开。
          </p>
        </div>
        <p style={{...sectionLabelStyle, color: "#8d96a0", letterSpacing: "0.04em", textTransform: "none"}}>
          支持 mp4 / mov / webm
        </p>
      </div>
    </button>
  );
}

function EmptyState() {
  return (
    <div
      style={{
        borderRadius: "14px",
        border: "1px dashed rgba(255,255,255,0.08)",
        background: "#111418",
        padding: "18px"
      }}
    >
      <p style={mutedTextStyle}>还没有选择视频。先从上面的上传入口添加一个本地素材。</p>
    </div>
  );
}

function AssetCard({
  asset,
  isActive,
  onSelect,
  onRemove
}: {
  asset: AssetItem;
  isActive: boolean;
  onSelect: () => void;
  onRemove: () => void;
}) {
  return (
    <div
      style={{
        borderRadius: "16px",
        border: isActive
          ? "1px solid rgba(121,192,255,0.45)"
          : "1px solid rgba(255,255,255,0.08)",
        background: isActive ? "#141b23" : "#111418",
        padding: "14px",
        display: "grid",
        gap: "12px"
      }}
    >
      <button
        type="button"
        onClick={onSelect}
        style={{
          appearance: "none",
          border: 0,
          background: "transparent",
          padding: 0,
          margin: 0,
          textAlign: "left",
          cursor: "pointer",
          color: "inherit",
          minWidth: 0
        }}
      >
        <p
          style={{
            ...textStyles.titleMedium,
            lineHeight: 1.4,
            wordBreak: "break-word"
          }}
          title={asset.name}
        >
          {asset.name}
        </p>
        <p style={{...mutedTextStyle, marginTop: "8px"}}>{formatAssetMeta(asset)}</p>
        <p style={{...mutedTextStyle, marginTop: "4px"}}>{renderAssetSyncLabel(asset)}</p>
      </button>

      <div style={{display: "flex", justifyContent: "space-between", gap: "10px"}}>
        <span
          style={{
            ...sectionLabelStyle,
            color: "rgba(121,192,255,0.88)"
          }}
        >
          Current
        </span>
        <button
          type="button"
          onClick={onRemove}
          style={{
            appearance: "none",
            border: 0,
            background: "transparent",
            color: "#8d96a0",
            fontSize: "12px",
            cursor: "pointer",
            padding: 0
          }}
        >
          Remove
        </button>
      </div>
    </div>
  );
}

function formatBytes(sizeBytes: number) {
  if (sizeBytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(sizeBytes / 1024))} KB`;
  }

  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatAssetMeta(asset: AssetItem) {
  const parts = [formatBytes(asset.sizeBytes)];

  if (asset.frameWidth && asset.frameHeight) {
    parts.push(`${asset.frameWidth}×${asset.frameHeight}`);
  }

  if (asset.durationSeconds) {
    parts.push(formatDuration(asset.durationSeconds));
  }

  parts.push(asset.origin);

  return parts.join(" · ");
}

function formatDuration(durationSeconds: number) {
  const minutes = Math.floor(durationSeconds / 60);
  const seconds = Math.max(0, Math.round(durationSeconds % 60));

  if (minutes <= 0) {
    return `${seconds}s`;
  }

  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
}

function renderAssetSyncLabel(asset: AssetItem) {
  if (asset.syncStatus === "REGISTERING") {
    return "Registering locally...";
  }

  if (asset.syncStatus === "FAILED") {
    return asset.errorMessage ?? "Registration failed";
  }

  if (asset.storageMode === "CLOUD") {
    return `Cloud-ready · ${asset.remoteAssetId ?? "remote asset"}`;
  }

  return `Local-ready · ${asset.remoteAssetId ?? "local asset"}`;
}
