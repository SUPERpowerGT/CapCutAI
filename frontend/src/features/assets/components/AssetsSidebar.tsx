"use client";

import type {ReactNode} from "react";
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
  onAddReferenceVideo,
  onAddSourceVideo,
  onRemoveAsset,
  onSelectReferenceAsset,
  onSelectSourceAsset
}: AssetsSidebarProps) {
  const selectedReferenceAsset =
    referenceAssets.find((item) => item.assetId === selectedReferenceAssetId) ?? null;
  const selectedSourceAsset =
    sourceAssets.find((item) => item.assetId === selectedSourceAssetId) ?? null;

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
          gap: "18px"
        }}
      >
        <div style={{display: "grid", gap: "4px"}}>
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

        {error ? <p style={{...mutedTextStyle, color: "#f2a3a3"}}>{error}</p> : null}

        <AssetGroupSection
          label="Reference Video"
          title="上传爆款参考视频"
          description="当前版本先只支持一个参考视频。重新上传会直接替换当前参考视频。"
          buttonLabel={isPicking || isRegistering ? "Selecting..." : "上传参考视频"}
          disabled={isPicking || isRegistering}
          onAdd={onAddReferenceVideo}
        >
          {selectedReferenceAsset ? (
            <AssetCard
              asset={selectedReferenceAsset}
              badge="Current Reference"
              isActive
              onSelect={() => onSelectReferenceAsset(selectedReferenceAsset.assetId)}
              onRemove={() => onRemoveAsset(selectedReferenceAsset.assetId)}
            />
          ) : (
            <EmptyState text="还没有参考视频。上传一个爆款视频做风格分析。" />
          )}
        </AssetGroupSection>

        <AssetGroupSection
          label="Source Videos"
          title="上传用户待剪视频"
          description="这里支持多个 source 视频。后续模型会基于当前 workspace 的 source 目录做分析与拆分。"
          buttonLabel={isPicking || isRegistering ? "Selecting..." : "上传源视频"}
          disabled={isPicking || isRegistering}
          onAdd={onAddSourceVideo}
        >
          {sourceAssets.length > 0 ? (
            <div style={{display: "grid", gap: "10px"}}>
              {sourceAssets.map((asset) => (
                <AssetCard
                  key={asset.assetId}
                  asset={asset}
                  badge={
                    asset.assetId === selectedSourceAsset?.assetId
                      ? "Current Source"
                      : "Source"
                  }
                  isActive={asset.assetId === selectedSourceAsset?.assetId}
                  onSelect={() => onSelectSourceAsset(asset.assetId)}
                  onRemove={() => onRemoveAsset(asset.assetId)}
                />
              ))}
            </div>
          ) : (
            <EmptyState text="还没有源视频。这里可以连续上传多个用户视频。" />
          )}
        </AssetGroupSection>
      </div>
    </section>
  );
}

function AssetGroupSection({
  label,
  title,
  description,
  buttonLabel,
  disabled,
  onAdd,
  children
}: {
  label: string;
  title: string;
  description: string;
  buttonLabel: string;
  disabled: boolean;
  onAdd: () => void;
  children: ReactNode;
}) {
  return (
    <section
      style={{
        display: "grid",
        gap: "12px",
        padding: "14px",
        borderRadius: "18px",
        border: "1px solid rgba(255,255,255,0.06)",
        background: "#111418"
      }}
    >
      <p style={sectionLabelStyle}>{label}</p>

      <button
        type="button"
        onClick={onAdd}
        disabled={disabled}
        style={{
          appearance: "none",
          width: "100%",
          minHeight: "132px",
          borderRadius: "16px",
          border: "1px dashed rgba(255,255,255,0.12)",
          background: "linear-gradient(180deg, #171a1e 0%, #111418 100%)",
          padding: "18px",
          display: "grid",
          placeItems: "center",
          textAlign: "center",
          cursor: disabled ? "default" : "pointer"
        }}
      >
        <div style={{display: "grid", gap: "8px", justifyItems: "center", maxWidth: "100%"}}>
          <div
            style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              display: "grid",
              placeItems: "center",
              background: "rgba(121,192,255,0.10)",
              color: "#78b7ff",
              fontSize: "16px",
              fontWeight: 700
            }}
          >
            ↑
          </div>
          <p style={{...textStyles.titleMedium, color: disabled ? "#8a949f" : "#dfe7ee"}}>
            {buttonLabel}
          </p>
          <p style={{...mutedTextStyle, maxWidth: "280px"}}>{title}</p>
          <p style={{...mutedTextStyle, maxWidth: "320px"}}>{description}</p>
        </div>
      </button>

      {children}
    </section>
  );
}

function EmptyState({text}: {text: string}) {
  return (
    <div
      style={{
        borderRadius: "14px",
        border: "1px dashed rgba(255,255,255,0.08)",
        background: "#0f1317",
        padding: "16px"
      }}
    >
      <p style={mutedTextStyle}>{text}</p>
    </div>
  );
}

function AssetCard({
  asset,
  badge,
  isActive,
  onSelect,
  onRemove
}: {
  asset: AssetItem;
  badge: string;
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
        background: isActive ? "#141b23" : "#0f1317",
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
            color: isActive ? "rgba(121,192,255,0.88)" : "#8d96a0"
          }}
        >
          {badge}
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
