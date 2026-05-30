"use client";

import type {AssetItem} from "../types/assets";

const sectionLabelStyle = {
  margin: 0,
  fontSize: "11px",
  letterSpacing: "0.12em",
  textTransform: "uppercase" as const,
  color: "#7d8792"
};

const mutedTextStyle = {
  margin: 0,
  color: "#8d96a0",
  fontSize: "12px",
  lineHeight: 1.5
};

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
        <div>
          <p style={sectionLabelStyle}>Assets</p>
        </div>
      </div>

      <div style={{minHeight: 0, overflow: "auto", padding: "16px"}}>
        <p style={mutedTextStyle}>
          这里是左侧资源主入口。当前已经支持本地参考视频和源视频的选择、登记、切换与移除；后续再接真实上传、目录管理和素材检索。
        </p>
        <WorkspaceAssetOverview
          workspaceTitle={workspaceTitle}
          referenceAsset={referenceAssets.find((item) => item.assetId === selectedReferenceAssetId) ?? null}
          sourceAsset={sourceAssets.find((item) => item.assetId === selectedSourceAssetId) ?? null}
        />
        <div style={{marginTop: "16px", display: "grid", gap: "10px"}}>
          <ActionCard
            title="Reference Video"
            description="选择爆款参考视频，用来做风格分析。"
            actionLabel={referenceAssets.length > 0 ? "Replace Reference" : "Add Reference"}
            currentAssetName={
              referenceAssets.find((item) => item.assetId === selectedReferenceAssetId)?.name ?? null
            }
            disabled={isPicking || isRegistering}
            onClick={onAddReferenceVideo}
          />
          <ActionCard
            title="Source Video"
            description="选择用户自己的源视频，用来生成风格化版本。"
            actionLabel={sourceAssets.length > 0 ? "Replace Source" : "Add Source"}
            currentAssetName={
              sourceAssets.find((item) => item.assetId === selectedSourceAssetId)?.name ?? null
            }
            disabled={isPicking || isRegistering}
            onClick={onAddSourceVideo}
          />
        </div>

        {error ? (
          <p style={{...mutedTextStyle, marginTop: "14px", color: "#f2a3a3"}}>{error}</p>
        ) : null}

        {isRegistering ? (
          <p style={{...mutedTextStyle, marginTop: "14px", color: "#9cc8ff"}}>
            正在登记当前本地资产。后续接云时，这一步会切到真实上传链路。
          </p>
        ) : null}

        <AssetSection
          title="Reference"
          emptyLabel="还没有参考视频。"
          assets={referenceAssets}
          selectedAssetId={selectedReferenceAssetId}
          onRemove={onRemoveAsset}
          onSelect={onSelectReferenceAsset}
        />
        <AssetSection
          title="Source"
          emptyLabel="还没有源视频。"
          assets={sourceAssets}
          selectedAssetId={selectedSourceAssetId}
          onRemove={onRemoveAsset}
          onSelect={onSelectSourceAsset}
        />
      </div>
    </section>
  );
}

function ActionCard({
  title,
  description,
  actionLabel,
  currentAssetName,
  disabled,
  onClick
}: {
  title: string;
  description: string;
  actionLabel: string;
  currentAssetName: string | null;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <div
      style={{
        borderRadius: "14px",
        border: "1px solid rgba(255,255,255,0.08)",
        background: "#111418",
        padding: "14px"
      }}
    >
      <div style={{display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px"}}>
        <div>
          <p style={{margin: 0, fontSize: "13px", fontWeight: 600, color: "#e9edf0"}}>{title}</p>
          <p style={{...mutedTextStyle, marginTop: "6px"}}>{description}</p>
          {currentAssetName ? (
            <p
              style={{
                ...mutedTextStyle,
                marginTop: "8px",
                color: "#cbd3da",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              }}
              title={currentAssetName}
            >
              Current: {currentAssetName}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={onClick}
          disabled={disabled}
          style={{
            appearance: "none",
            border: "1px solid rgba(255,255,255,0.10)",
            background: disabled ? "#1a1d21" : "#191d21",
            color: disabled ? "#74808b" : "#e5ecf2",
            borderRadius: "999px",
            padding: "8px 12px",
            fontSize: "12px",
            cursor: disabled ? "default" : "pointer"
          }}
        >
          {disabled ? "Selecting..." : actionLabel}
        </button>
      </div>
    </div>
  );
}

function AssetSection({
  title,
  emptyLabel,
  assets,
  selectedAssetId,
  onRemove,
  onSelect
}: {
  title: string;
  emptyLabel: string;
  assets: AssetItem[];
  selectedAssetId: string | null;
  onRemove: (assetId: string) => void;
  onSelect: (assetId: string) => void;
}) {
  return (
    <section style={{marginTop: "18px"}}>
      <p style={sectionLabelStyle}>{title}</p>

      {assets.length === 0 ? (
        <div
          style={{
            marginTop: "10px",
            borderRadius: "14px",
            border: "1px dashed rgba(255,255,255,0.08)",
            background: "#111418",
            padding: "16px"
          }}
        >
          <p style={mutedTextStyle}>{emptyLabel}</p>
        </div>
      ) : (
        <div style={{marginTop: "10px", display: "grid", gap: "10px"}}>
          {assets.map((asset) => {
            const isActive = selectedAssetId === asset.assetId;

            return (
              <div
                key={asset.assetId}
                style={{
                  borderRadius: "14px",
                  border: isActive
                    ? "1px solid rgba(121,192,255,0.55)"
                    : "1px solid rgba(255,255,255,0.08)",
                  background: isActive ? "#141b23" : "#111418",
                  padding: "14px"
                }}
              >
                <div style={{display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px"}}>
                  <button
                    type="button"
                    onClick={() => onSelect(asset.assetId)}
                    style={{
                      appearance: "none",
                      border: 0,
                      background: "transparent",
                      padding: 0,
                      margin: 0,
                      minWidth: 0,
                      textAlign: "left",
                      cursor: "pointer",
                      color: "inherit",
                      flex: 1
                    }}
                  >
                    <p
                      style={{
                        margin: 0,
                        fontSize: "13px",
                        fontWeight: 600,
                        color: "#e9edf0",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap"
                      }}
                      title={asset.name}
                    >
                      {asset.name}
                    </p>
                    <p style={{...mutedTextStyle, marginTop: "6px"}}>
                      {isActive ? "Current · " : ""}
                      {formatAssetMeta(asset)}
                    </p>
                    <p style={{...mutedTextStyle, marginTop: "4px"}}>
                      {renderAssetSyncLabel(asset)}
                    </p>
                  </button>
                  <button
                    type="button"
                    onClick={() => onRemove(asset.assetId)}
                    style={{
                      appearance: "none",
                      border: 0,
                      background: "transparent",
                      color: "#8d96a0",
                      fontSize: "18px",
                      lineHeight: 1,
                      cursor: "pointer"
                    }}
                    aria-label={`Remove ${asset.name}`}
                  >
                    ×
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function WorkspaceAssetOverview({
  workspaceTitle,
  referenceAsset,
  sourceAsset
}: {
  workspaceTitle: string;
  referenceAsset: AssetItem | null;
  sourceAsset: AssetItem | null;
}) {
  return (
    <section
      style={{
        marginTop: "14px",
        borderRadius: "14px",
        border: "1px solid rgba(255,255,255,0.08)",
        background: "#111418",
        padding: "14px"
      }}
    >
      <p style={sectionLabelStyle}>Current Workspace</p>
      <p
        style={{
          margin: "6px 0 0",
          fontSize: "14px",
          fontWeight: 600,
          color: "#e9edf0"
        }}
      >
        {workspaceTitle}
      </p>
      <div style={{marginTop: "10px", display: "grid", gap: "10px"}}>
        <WorkspaceAssetRow
          label="Reference"
          value={referenceAsset?.name ?? "未选择参考视频"}
          isReady={Boolean(referenceAsset)}
        />
        <WorkspaceAssetRow
          label="Source"
          value={sourceAsset?.name ?? "未选择源视频"}
          isReady={Boolean(sourceAsset)}
        />
      </div>
    </section>
  );
}

function WorkspaceAssetRow({
  label,
  value,
  isReady
}: {
  label: string;
  value: string;
  isReady: boolean;
}) {
  return (
    <div
      style={{
        display: "grid",
        gap: "4px",
        padding: "10px 12px",
        borderRadius: "12px",
        border: isReady
          ? "1px solid rgba(121,192,255,0.28)"
          : "1px solid rgba(255,255,255,0.06)",
        background: isReady ? "#141b23" : "#0f1317"
      }}
    >
      <span style={sectionLabelStyle}>{label}</span>
      <span
        style={{
          fontSize: "12px",
          color: isReady ? "#e9edf0" : "#8d96a0",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap"
        }}
        title={value}
      >
        {value}
      </span>
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
