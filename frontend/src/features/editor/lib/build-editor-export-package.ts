import type {AssetItem} from "../../assets/types/assets";
import type {
  EditingExperience,
  EditingJob,
  EditorExportPackage,
  RenderResult,
  SourceMaterial,
  TimelinePlan,
  TimelinePlanClip,
  WorkspaceTimelineClip
} from "../types/editor-preview";

function toMs(seconds?: number) {
  return Math.max(0, Math.round((seconds ?? 0) * 1000));
}

function toStableIdPart(value: string) {
  return value.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 64);
}

function getMaterialOffsetMs(sourceMaterials: SourceMaterial[], materialIndex: number) {
  return sourceMaterials
    .slice(0, materialIndex)
    .reduce((total, material) => total + Math.max(0, material.durationMs), 0);
}

function buildVideoClips(
  sourceAssets: AssetItem[],
  sourceMaterials: SourceMaterial[],
  workspaceTimelineClips: WorkspaceTimelineClip[]
) {
  if (workspaceTimelineClips.length > 0) {
    return [...workspaceTimelineClips]
      .sort((left, right) => left.timelineStartMs - right.timelineStartMs)
      .map((clip): TimelinePlanClip => {
      const asset = sourceAssets.find((item) => item.assetId === clip.assetId);
      const timelineClip: TimelinePlanClip = {
        clipId: clip.clipId,
        assetId: clip.assetId,
        type: "video",
        startMs: clip.timelineStartMs,
        durationMs: clip.durationMs,
        sourceStartMs: clip.sourceStartMs,
        label: clip.label
      };

      if (asset) {
        timelineClip.label = `${asset.name} · ${clip.label}`;
      }

      return timelineClip;
    });
  }

  if (sourceAssets.length === 0 || sourceMaterials.length === 0) {
    return [];
  }

  return sourceMaterials.flatMap((sourceMaterial, materialIndex) => {
    const materialOffsetMs = getMaterialOffsetMs(sourceMaterials, materialIndex);
    const asset = sourceAssets[materialIndex % sourceAssets.length];

    return sourceMaterial.visualShots.map((shot, shotIndex): TimelinePlanClip => {
      const durationMs = Math.max(1000, shot.endMs - shot.startMs);

      return {
        clipId: `clip_video_${materialIndex + 1}_${shotIndex + 1}_${toStableIdPart(asset.assetId)}`,
        assetId: asset.assetId,
        sourceMaterialId: sourceMaterial.sourceMaterialId,
        type: "video",
        startMs: materialOffsetMs + shot.startMs,
        durationMs,
        sourceStartMs: shot.startMs,
        label: `${asset.name} · ${shot.shotType}`
      };
    });
  });
}

function buildSubtitleClips(sourceMaterials: SourceMaterial[], targetDurationMs: number) {
  return sourceMaterials.flatMap((sourceMaterial, materialIndex) => {
    const materialOffsetMs = getMaterialOffsetMs(sourceMaterials, materialIndex);

    return sourceMaterial.transcript.sentences.map((sentence, sentenceIndex): TimelinePlanClip => {
      const localDurationMs = Math.max(400, sentence.endMs - sentence.startMs);

      return {
        clipId: `clip_caption_${materialIndex + 1}_${sentenceIndex + 1}_${toStableIdPart(
          String(sentence.startMs)
        )}`,
        sourceMaterialId: sourceMaterial.sourceMaterialId,
        type: "subtitle",
        startMs: Math.min(materialOffsetMs + sentence.startMs, targetDurationMs),
        durationMs: Math.min(localDurationMs, targetDurationMs),
        label: sentence.text
      };
    });
  });
}

function buildAudioClips(sourceMaterials: SourceMaterial[]) {
  return sourceMaterials.flatMap((sourceMaterial, materialIndex) => {
    const materialOffsetMs = getMaterialOffsetMs(sourceMaterials, materialIndex);

    return sourceMaterial.dropsMs.map((dropMs, dropIndex): TimelinePlanClip => ({
      clipId: `clip_audio_${materialIndex + 1}_${dropIndex + 1}_${toStableIdPart(String(dropMs))}`,
      sourceMaterialId: sourceMaterial.sourceMaterialId,
      type: "audio",
      startMs: materialOffsetMs + dropMs,
      durationMs: 1000,
      label: `${sourceMaterial.sourceCaseId} · Drop ${dropIndex + 1}`
    }));
  });
}

function buildOverlayClips(sourceMaterials: SourceMaterial[]) {
  return sourceMaterials.flatMap((sourceMaterial, materialIndex) => {
    const materialOffsetMs = getMaterialOffsetMs(sourceMaterials, materialIndex);

    return sourceMaterial.visualShots
      .filter(
        (shot) =>
          shot.editingUtility === "HOOK_OPENER" || shot.editingUtility === "EMPHASIS_HIGHLIGHT"
      )
      .map((shot, shotIndex): TimelinePlanClip => ({
        clipId: `clip_overlay_${materialIndex + 1}_${shotIndex + 1}_${toStableIdPart(
          String(shot.startMs)
        )}`,
        sourceMaterialId: sourceMaterial.sourceMaterialId,
        type: "overlay",
        startMs: materialOffsetMs + shot.startMs,
        durationMs: Math.max(1000, shot.endMs - shot.startMs),
        label: `${sourceMaterial.sourceCaseId} · ${shot.editingUtility}`
      }));
  });
}

export function buildTimelinePlan({
  workspaceId,
  sourceAssets,
  experience,
  sourceMaterials,
  workspaceTimelineClips = []
}: {
  workspaceId: string;
  sourceAssets: AssetItem[];
  experience: EditingExperience;
  sourceMaterials: SourceMaterial[];
  workspaceTimelineClips?: WorkspaceTimelineClip[];
}): TimelinePlan {
  const assetDurationMs = sourceAssets.reduce((total, asset) => total + toMs(asset.durationSeconds), 0);
  const sourceMaterialDurationMs = sourceMaterials.reduce(
    (total, sourceMaterial) => total + Math.max(0, sourceMaterial.durationMs),
    0
  );
  const workspaceTimelineDurationMs = workspaceTimelineClips.reduce(
    (maxDurationMs, clip) => Math.max(maxDurationMs, clip.timelineStartMs + Math.max(0, clip.durationMs)),
    0
  );
  const targetDurationMs =
    workspaceTimelineDurationMs > 0
      ? workspaceTimelineDurationMs
      :
    sourceMaterialDurationMs > 0
      ? sourceMaterialDurationMs
      : experience.sampleVideoDurationMs > 0
      ? experience.sampleVideoDurationMs
      : Math.max(assetDurationMs, 15000);

  const timelineId = `timeline_${toStableIdPart(workspaceId)}_${toStableIdPart(
    experience.styleId
  )}_${sourceAssets.length}_${sourceMaterials.length}`;

  return {
    timelineId,
    workspaceId,
    styleId: experience.styleId,
    sourceAssetIds:
      workspaceTimelineClips.length > 0
        ? Array.from(new Set(workspaceTimelineClips.map((clip) => clip.assetId)))
        : sourceAssets.map((asset) => asset.assetId),
    sourceMaterialIds: sourceMaterials.map((sourceMaterial) => sourceMaterial.sourceMaterialId),
    targetDurationMs,
    tracks: [
      {
        trackId: "track_video_main",
        type: "video",
        clips: buildVideoClips(sourceAssets, sourceMaterials, workspaceTimelineClips)
      },
      {
        trackId: "track_caption_main",
        type: "subtitle",
        clips: buildSubtitleClips(sourceMaterials, targetDurationMs)
      },
      {
        trackId: "track_overlay_main",
        type: "overlay",
        clips: buildOverlayClips(sourceMaterials)
      },
      {
        trackId: "track_audio_main",
        type: "audio",
        clips: buildAudioClips(sourceMaterials)
      }
    ]
  };
}

export function buildEditingJob(timelinePlan: TimelinePlan): EditingJob {
  return {
    jobId: `editing_job_${toStableIdPart(timelinePlan.timelineId)}`,
    timelineId: timelinePlan.timelineId,
    renderer: "hyperframes",
    status: "draft",
    compositionPath: `ai-service/output/plans/${timelinePlan.timelineId}.hyperframes/`,
    outputPath: `ai-service/output/renders/${timelinePlan.timelineId}.final.mp4`,
    renderHints: {
      fps: 30,
      width: 1080,
      height: 1920,
      format: "mp4"
    }
  };
}

export function buildRenderResult(editingJob: EditingJob, previewAssetId?: string): RenderResult {
  return {
    renderId: `render_${toStableIdPart(editingJob.jobId)}`,
    jobId: editingJob.jobId,
    status: "not_started",
    outputPath: editingJob.outputPath,
    previewAssetId
  };
}

export function buildEditorExportPackage({
  workspaceId,
  sourceAssets,
  selectedSourceAsset,
  workspaceTimelineClips = [],
  experience,
  sourceMaterials
}: {
  workspaceId: string;
  sourceAssets: AssetItem[];
  selectedSourceAsset: AssetItem | null;
  workspaceTimelineClips?: WorkspaceTimelineClip[];
  experience: EditingExperience;
  sourceMaterials: SourceMaterial[];
}): EditorExportPackage {
  const timelinePlan = buildTimelinePlan({
    workspaceId,
    sourceAssets,
    experience,
    sourceMaterials,
    workspaceTimelineClips
  });
  const editingJob = buildEditingJob(timelinePlan);

  return {
    exportedAt: new Date().toISOString(),
    sourceAssets,
    editingExperience: experience,
    sourceMaterials,
    timelinePlan,
    editingJob,
    renderResult: buildRenderResult(editingJob, selectedSourceAsset?.assetId)
  };
}

export function downloadEditorExportPackage(exportPackage: EditorExportPackage) {
  const content = JSON.stringify(exportPackage, null, 2);
  const blob = new Blob([content], {type: "application/json"});
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = `${exportPackage.timelinePlan.timelineId}.editing-package.json`;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}
