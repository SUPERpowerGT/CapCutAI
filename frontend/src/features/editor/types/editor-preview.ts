import type {AssetItem} from "../../assets/types/assets";

export type EditingExperience = {
  experienceId: string;
  styleId: string;
  category: string;
  styleName: string;
  pacingStyle: string;
  visualTheme: string;
  tags: string[];
  sampleVideoDurationMs: number;
  storylinePhases: Array<{
    phaseId: string;
    narrativeGoal: string;
    startMs: number;
    endMs: number;
    durationMs: number;
  }>;
  dynamicBeatCount: number;
};

export type SourceMaterial = {
  sourceMaterialId: string;
  sourceCaseId: string;
  durationMs: number;
  bpm: number;
  beatsMs: number[];
  dropsMs: number[];
  transcript: {
    fullText: string;
    sentences: Array<{
      text: string;
      startMs: number;
      endMs: number;
    }>;
  };
  visualShots: Array<{
    index: number;
    startMs: number;
    endMs: number;
    shotType: string;
    contentType: string;
    emotionalTone: string;
    semanticPrompt: string;
    cameraMotionEffect: string;
    editingUtility: string;
  }>;
  optionalStyleHints?: {
    styleId?: string;
    storylinePhaseCount?: number;
    narrativeGoals?: string[];
  };
};

export type TimelinePlanTrackType = "video" | "subtitle" | "overlay" | "audio";

export type TimelinePlanClip = {
  clipId: string;
  assetId?: string;
  sourceMaterialId?: string;
  type: TimelinePlanTrackType;
  startMs: number;
  durationMs: number;
  sourceStartMs?: number;
  label: string;
  phaseId?: string;
};

export type TimelinePlan = {
  timelineId: string;
  workspaceId: string;
  styleId: string;
  sourceAssetIds: string[];
  sourceMaterialIds: string[];
  targetDurationMs: number;
  tracks: Array<{
    trackId: string;
    type: TimelinePlanTrackType;
    clips: TimelinePlanClip[];
  }>;
};

export type EditingJob = {
  jobId: string;
  timelineId: string;
  renderer: "hyperframes";
  status: "draft";
  compositionPath: string;
  outputPath: string;
  renderHints: {
    fps: number;
    width: number;
    height: number;
    format: "mp4";
  };
};

export type RenderResult = {
  renderId: string;
  jobId: string;
  status: "not_started";
  outputPath: string;
  previewAssetId?: string;
};

export type EditorExportPackage = {
  exportedAt: string;
  sourceAssets: AssetItem[];
  editingExperience: EditingExperience;
  sourceMaterials: SourceMaterial[];
  timelinePlan: TimelinePlan;
  editingJob: EditingJob;
  renderResult: RenderResult;
};
