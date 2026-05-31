"use client";

import {useState} from "react";
import type {CSSProperties, MouseEvent, ReactNode} from "react";
import {openWorkspaceAssetLocation} from "../api/desktop-workspace-assets";
import type {AssetItem} from "../types/assets";
import {textStyles} from "../../../shared/design/typography";
import {isDesktopRuntime} from "../../workspace/api/desktop-workspace";

const sectionLabelStyle = textStyles.sectionLabel;
const mutedTextStyle = textStyles.bodySmall;

type AssetsSidebarProps = {
  workspaceTitle: string;
  referenceAssets: AssetItem[];
  selectedReferenceAssetId: string | null;
  selectedPreviewAssetId: string | null;
  sourceAssets: AssetItem[];
  selectedSourceAssetId: string | null;
  isPicking: boolean;
  isRegistering: boolean;
  error: string | null;
  onAddReferenceVideo: () => void;
  onAddSourceVideo: () => void;
  onRemoveAsset: (assetId: string) => void;
  onSelectReferenceAsset: (assetId: string) => void;
  onSelectSourceAsset: (assetId: string) => void;
  onStartSourceTimelineDrag: (asset: AssetItem, event: MouseEvent<HTMLDivElement>) => void;
};

export function AssetsSidebar({
  workspaceTitle,
  referenceAssets,
  selectedReferenceAssetId,
  selectedPreviewAssetId,
  sourceAssets,
  selectedSourceAssetId,
  isPicking,
  isRegistering,
  error,
  onAddReferenceVideo,
  onAddSourceVideo,
  onRemoveAsset,
  onSelectReferenceAsset,
  onSelectSourceAsset,
  onStartSourceTimelineDrag
}: AssetsSidebarProps) {
  const selectedReferenceAsset =
    referenceAssets.find((item) => item.assetId === selectedReferenceAssetId) ?? null;
  const isBusy = isPicking || isRegistering;

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
          justifyContent: "space-between",
          gap: "12px",
          padding: "0 16px",
          borderBottom: "1px solid rgba(255,255,255,0.06)"
        }}
      >
        <p style={sectionLabelStyle}>Assets</p>
        <span style={{...mutedTextStyle, fontSize: "11px"}}>
          {sourceAssets.length} source
        </span>
      </div>

      <div
        style={{
          minHeight: 0,
          overflow: "hidden",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "14px"
        }}
      >
        <WorkspaceCard workspaceTitle={workspaceTitle} />

        {error ? <p style={{...mutedTextStyle, color: "#f2a3a3"}}>{error}</p> : null}

        <CompactSection
          label="Reference"
          actionLabel={isBusy ? "Selecting..." : "Add"}
          disabled={isBusy}
          onAction={onAddReferenceVideo}
        >
          {selectedReferenceAsset ? (
            <PrimaryAssetCard
              asset={selectedReferenceAsset}
              badge={selectedPreviewAssetId === selectedReferenceAsset.assetId ? "Previewing" : "Reference"}
              isActive={selectedPreviewAssetId === selectedReferenceAsset.assetId}
              onSelect={() => onSelectReferenceAsset(selectedReferenceAsset.assetId)}
              onRemove={() => onRemoveAsset(selectedReferenceAsset.assetId)}
            />
          ) : (
            <EmptyState text="Add one reference video" />
          )}
        </CompactSection>

        <CompactSection
          label="Source"
          actionLabel={isBusy ? "Selecting..." : "Add"}
          disabled={isBusy}
          onAction={onAddSourceVideo}
          helper="Tap any clip to preview"
          style={{
            flex: "1 1 0",
            minHeight: 0,
            gridTemplateRows: "auto minmax(0, 1fr)"
          }}
        >
          {sourceAssets.length > 0 ? (
            <div
              style={{
                minHeight: 0,
                overflowY: "auto",
                overflowX: "hidden",
                paddingRight: "4px"
              }}
            >
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr",
                  gap: "10px",
                  minWidth: 0
                }}
              >
                {sourceAssets.map((asset) => (
                  <SourceStripCard
                    key={asset.assetId}
                    asset={asset}
                    isActive={asset.assetId === selectedSourceAssetId}
                    onStartTimelineDrag={onStartSourceTimelineDrag}
                    onSelect={() => onSelectSourceAsset(asset.assetId)}
                    onRemove={() => onRemoveAsset(asset.assetId)}
                  />
                ))}
              </div>
            </div>
          ) : (
            <EmptyState text="Add source videos" />
          )}
        </CompactSection>
      </div>
    </section>
  );
}

function WorkspaceCard({workspaceTitle}: {workspaceTitle: string}) {
  return (
    <div
      style={{
        display: "grid",
        gap: "4px",
        padding: "12px 14px",
        borderRadius: "14px",
        border: "1px solid rgba(255,255,255,0.06)",
        background: "#101417"
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
  );
}

function CompactSection({
  label,
  actionLabel,
  disabled,
  onAction,
  helper,
  style,
  children
}: {
  label: string;
  actionLabel: string;
  disabled: boolean;
  onAction: () => void;
  helper?: string;
  style?: CSSProperties;
  children: ReactNode;
}) {
  return (
    <section
      style={{
        display: "grid",
        gap: "10px",
        padding: "14px",
        borderRadius: "18px",
        border: "1px solid rgba(255,255,255,0.06)",
        background: "#111418",
        ...style
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "10px"
        }}
      >
        <div style={{display: "grid", gap: "4px"}}>
          <p style={sectionLabelStyle}>{label}</p>
          {helper ? (
            <p style={{...mutedTextStyle, fontSize: "11px", color: "#7f8a95"}}>{helper}</p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={onAction}
          disabled={disabled}
          style={{
            appearance: "none",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "999px",
            background: disabled
              ? "rgba(255,255,255,0.04)"
              : "linear-gradient(180deg, rgba(121,192,255,0.22), rgba(121,192,255,0.12))",
            color: disabled ? "#7f8a95" : "#d9ecff",
            padding: "8px 13px",
            cursor: disabled ? "default" : "pointer",
            fontSize: "11px",
            fontWeight: 600,
            lineHeight: 1
          }}
        >
          {actionLabel}
        </button>
      </div>

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
        padding: "14px"
      }}
    >
      <p style={mutedTextStyle}>{text}</p>
    </div>
  );
}

function PrimaryAssetCard({
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
      draggable
      onDragStart={(event) => {
        event.dataTransfer.effectAllowed = "copy";
        event.dataTransfer.setData("text/plain", asset.assetId);
        event.dataTransfer.setData("application/x-capcutai-source-asset", asset.assetId);
      }}
      style={{
        borderRadius: "16px",
        border: isActive
          ? "1px solid rgba(121,192,255,0.45)"
          : "1px solid rgba(255,255,255,0.08)",
        background: isActive ? "#141b23" : "#0f1317",
        padding: "12px",
        display: "grid",
        gap: "10px"
      }}
    >
      <button
        type="button"
        onClick={onSelect}
        draggable={false}
        style={{
          appearance: "none",
          border: 0,
          background: "transparent",
          padding: 0,
          margin: 0,
          textAlign: "left",
          cursor: "pointer",
          color: "inherit",
          minWidth: 0,
          display: "grid",
          gap: "10px"
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "96px minmax(0, 1fr)",
            gap: "10px",
            alignItems: "center"
          }}
        >
          <PreviewThumb asset={asset} compact />
          <div style={{display: "grid", gap: "4px", minWidth: 0}}>
            <p
              style={{
                ...textStyles.bodySmallStrong,
                color: isActive ? "#e7f2ff" : "#d3dbe3",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              }}
              title={asset.name}
            >
              {asset.name}
            </p>
            <p
              style={{
                ...mutedTextStyle,
                fontSize: "11px",
                color: isActive ? "#93a8bc" : "#7f8a95",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              }}
              title={formatAssetMeta(asset)}
            >
              {formatAssetMeta(asset)}
            </p>
          </div>
        </div>
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
        <AssetActionsMenu asset={asset} onRemove={onRemove} />
      </div>
    </div>
  );
}

function SourceStripCard({
  asset,
  isActive,
  onStartTimelineDrag,
  onSelect,
  onRemove
}: {
  asset: AssetItem;
  isActive: boolean;
  onStartTimelineDrag: (asset: AssetItem, event: MouseEvent<HTMLDivElement>) => void;
  onSelect: () => void;
  onRemove: () => void;
}) {
  return (
    <div
      onMouseDown={(event) => {
        if (event.button !== 0) {
          return;
        }

        onStartTimelineDrag(asset, event);
      }}
      style={{
        borderRadius: "16px",
        border: isActive
          ? "1px solid rgba(121,192,255,0.44)"
          : "1px solid rgba(255,255,255,0.08)",
        background: isActive
          ? "linear-gradient(180deg, #16202a 0%, #10161d 100%)"
          : "#0f1317",
        padding: "10px",
        display: "grid",
        gap: "10px",
        minWidth: 0
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
          minWidth: 0,
          display: "grid",
          gap: "10px"
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "96px minmax(0, 1fr)",
            gap: "10px",
            alignItems: "center"
          }}
        >
          <PreviewThumb asset={asset} compact />
          <div style={{display: "grid", gap: "4px", minWidth: 0}}>
            <p
              style={{
                ...textStyles.bodySmallStrong,
                color: isActive ? "#e7f2ff" : "#d3dbe3",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              }}
              title={asset.name}
            >
              {asset.name}
            </p>
            <p
              style={{
                ...mutedTextStyle,
                fontSize: "11px",
                color: isActive ? "#93a8bc" : "#7f8a95",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              }}
              title={formatAssetMeta(asset)}
            >
              {formatAssetMeta(asset)}
            </p>
          </div>
        </div>
      </button>

      <div style={{display: "flex", justifyContent: "space-between", gap: "8px"}}>
        <span
          style={{
            ...sectionLabelStyle,
            color: isActive ? "rgba(121,192,255,0.88)" : "#6f7b86"
          }}
        >
          {isActive ? "Previewing" : "Clip"}
        </span>
        <AssetActionsMenu asset={asset} onRemove={onRemove} />
      </div>
    </div>
  );
}

function AssetActionsMenu({asset, onRemove}: {asset: AssetItem; onRemove: () => void}) {
  const [isOpen, setIsOpen] = useState(false);
  const canOpenLocation = isDesktopRuntime() && Boolean(asset.workspaceFilePath);

  async function handleOpenLocation(event: MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
    if (!asset.workspaceFilePath) {
      return;
    }

    try {
      await openWorkspaceAssetLocation(asset.workspaceFilePath);
    } finally {
      setIsOpen(false);
    }
  }

  function handleToggle(event: MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
    setIsOpen((current) => !current);
  }

  function handleRemove(event: MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
    setIsOpen(false);
    onRemove();
  }

  return (
    <div style={{position: "relative"}}>
      <button type="button" onClick={handleToggle} aria-label="Asset actions" style={ghostActionStyle}>
        ...
      </button>
      {isOpen ? (
        <div
          style={{
            position: "absolute",
            right: 0,
            bottom: "calc(100% + 8px)",
            minWidth: "168px",
            padding: "6px",
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.08)",
            background: "#161b20",
            boxShadow: "0 16px 36px rgba(0,0,0,0.32)",
            display: "grid",
            gap: "4px",
            zIndex: 10
          }}
        >
          <button
            type="button"
            onClick={handleOpenLocation}
            disabled={!canOpenLocation}
            style={{
              ...menuActionStyle,
              color: canOpenLocation ? "#dce7f2" : "#73808d",
              cursor: canOpenLocation ? "pointer" : "default"
            }}
          >
            Open file location
          </button>
          <button type="button" onClick={handleRemove} style={menuActionStyle}>
            Remove
          </button>
        </div>
      ) : null}
    </div>
  );
}

function PreviewThumb({asset, compact}: {asset: AssetItem; compact: boolean}) {
  return (
    <div
      style={{
        width: "100%",
        aspectRatio: "16 / 9",
        borderRadius: compact ? "10px" : "12px",
        overflow: "hidden",
        background:
          "linear-gradient(135deg, rgba(121,192,255,0.12), rgba(255,153,102,0.10)), #090c10",
        border: "1px solid rgba(255,255,255,0.06)",
        display: "grid",
        placeItems: "center"
      }}
    >
      {asset.previewImageUrl ? (
        <img
          src={asset.previewImageUrl}
          alt={`${asset.name} preview`}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            display: "block",
            background: "#090c10"
          }}
        />
      ) : asset.objectUrl ? (
        <video
          src={asset.objectUrl}
          muted
          playsInline
          preload="metadata"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            display: "block",
            background: "#090c10"
          }}
        />
      ) : (
        <span style={{...textStyles.titleSmall, color: "#89beff"}}>VIDEO</span>
      )}
    </div>
  );
}

const ghostActionStyle = {
  appearance: "none",
  border: 0,
  background: "transparent",
  color: "#8d96a0",
  fontSize: "11px",
  cursor: "pointer",
  padding: 0,
  lineHeight: 1
} as const;

const menuActionStyle = {
  appearance: "none",
  border: 0,
  background: "transparent",
  borderRadius: "8px",
  color: "#dce7f2",
  fontSize: "11px",
  textAlign: "left",
  padding: "8px 10px",
  cursor: "pointer"
} as const;

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
