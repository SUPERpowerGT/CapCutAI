"use client";

import {useMemo, useState} from "react";
import type {AssetItem} from "../../assets/types/assets";
import {loadMockEditingExperience} from "../data/mock-editing-experience";
import {selectMockSourceMaterials} from "../data/mock-source-material";
import {
  buildEditorExportPackage,
  downloadEditorExportPackage
} from "../lib/build-editor-export-package";
import type {EditorExportPackage} from "../types/editor-preview";
import {PreviewViewport} from "./PreviewViewport";
import {TimelinePanel} from "./TimelinePanel";

type EditorSurfaceProps = {
  title: string;
  subtitle?: string;
  workspaceId: string;
  sourceAssets: AssetItem[];
  selectedSourceAsset: AssetItem | null;
  previewSource?: {
    objectUrl?: string;
    name: string;
    mimeType: string;
  } | null;
  previewHeightPercent: number;
  isBottomPaneCollapsed?: boolean;
  onResizeStart: () => void;
};

export function EditorSurface({
  title,
  subtitle,
  workspaceId,
  sourceAssets,
  selectedSourceAsset,
  previewSource,
  previewHeightPercent,
  isBottomPaneCollapsed = false,
  onResizeStart
}: EditorSurfaceProps) {
  const editingExperience = useMemo(() => loadMockEditingExperience(), []);
  const sourceMaterials = useMemo(() => selectMockSourceMaterials(sourceAssets.length), [sourceAssets.length]);
  const [lastExportPackage, setLastExportPackage] = useState<EditorExportPackage | null>(null);

  const draftExportPackage = useMemo(
    () =>
      buildEditorExportPackage({
        workspaceId,
        sourceAssets,
        selectedSourceAsset,
        experience: editingExperience,
        sourceMaterials
      }),
    [editingExperience, selectedSourceAsset, sourceAssets, sourceMaterials, workspaceId]
  );

  function exportEditingPackage() {
    setLastExportPackage(draftExportPackage);
    downloadEditorExportPackage(draftExportPackage);
  }

  return (
    <section
      style={{
        minHeight: 0,
        display: "grid",
        gridTemplateRows: isBottomPaneCollapsed
          ? "minmax(0, 1fr)"
          : `minmax(220px, ${previewHeightPercent}%) 8px minmax(180px, ${100 - previewHeightPercent}%)`,
        background: "#121518"
      }}
    >
      <PreviewViewport
        title={title}
        subtitle={subtitle}
        previewSource={previewSource}
        selectedSourceAsset={selectedSourceAsset}
        sourceAssetCount={sourceAssets.length}
        editingExperience={editingExperience}
        sourceMaterials={sourceMaterials}
      />
      {!isBottomPaneCollapsed ? (
        <>
          <button
            type="button"
            aria-label="Resize preview and timeline"
            onMouseDown={onResizeStart}
            style={{
              appearance: "none",
              border: 0,
              padding: 0,
              margin: 0,
              cursor: "row-resize",
              background: "transparent",
              position: "relative"
            }}
          >
            <span
              style={{
                position: "absolute",
                top: "50%",
                left: 0,
                right: 0,
                height: "1px",
                background: "rgba(255,255,255,0.12)",
                transform: "translateY(-50%)"
              }}
            />
          </button>
          <TimelinePanel
            sourceAssets={sourceAssets}
            editingExperience={editingExperience}
            sourceMaterials={sourceMaterials}
            timelinePlan={draftExportPackage.timelinePlan}
            editingJob={draftExportPackage.editingJob}
            lastExportPackage={lastExportPackage}
            onExportEditingPackage={exportEditingPackage}
          />
        </>
      ) : null}
    </section>
  );
}
