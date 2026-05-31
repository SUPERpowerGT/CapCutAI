from typing import Literal

from pydantic import BaseModel, Field


class AssetItemModel(BaseModel):
    asset_id: str = Field(alias="assetId")
    workspace_id: str = Field(alias="workspaceId")
    category: str
    slot: str
    origin: str
    storage_mode: str = Field(alias="storageMode")
    sync_status: str = Field(alias="syncStatus")
    name: str
    mime_type: str = Field(alias="mimeType")
    size_bytes: int = Field(alias="sizeBytes")
    added_at: str = Field(alias="addedAt")
    duration_seconds: float | None = Field(default=None, alias="durationSeconds")
    frame_width: int | None = Field(default=None, alias="frameWidth")
    frame_height: int | None = Field(default=None, alias="frameHeight")
    object_url: str | None = Field(default=None, alias="objectUrl")
    remote_asset_id: str | None = Field(default=None, alias="remoteAssetId")
    error_message: str | None = Field(default=None, alias="errorMessage")

    model_config = {"populate_by_name": True}


class EditingExperiencePhaseModel(BaseModel):
    phase_id: str = Field(alias="phaseId")
    narrative_goal: str = Field(alias="narrativeGoal")
    start_ms: int = Field(alias="startMs")
    end_ms: int = Field(alias="endMs")
    duration_ms: int = Field(alias="durationMs")

    model_config = {"populate_by_name": True}


class EditingExperienceModel(BaseModel):
    experience_id: str = Field(alias="experienceId")
    style_id: str = Field(alias="styleId")
    category: str
    style_name: str = Field(alias="styleName")
    pacing_style: str = Field(alias="pacingStyle")
    visual_theme: str = Field(alias="visualTheme")
    tags: list[str] = Field(default_factory=list)
    sample_video_duration_ms: int = Field(alias="sampleVideoDurationMs")
    storyline_phases: list[EditingExperiencePhaseModel] = Field(
        default_factory=list, alias="storylinePhases"
    )
    dynamic_beat_count: int = Field(alias="dynamicBeatCount")

    model_config = {"populate_by_name": True}


class SourceMaterialSentenceModel(BaseModel):
    text: str
    start_ms: int = Field(alias="startMs")
    end_ms: int = Field(alias="endMs")

    model_config = {"populate_by_name": True}


class SourceMaterialTranscriptModel(BaseModel):
    full_text: str = Field(alias="fullText")
    sentences: list[SourceMaterialSentenceModel] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class SourceMaterialVisualShotModel(BaseModel):
    index: int
    start_ms: int = Field(alias="startMs")
    end_ms: int = Field(alias="endMs")
    shot_type: str = Field(alias="shotType")
    content_type: str = Field(alias="contentType")
    emotional_tone: str = Field(alias="emotionalTone")
    semantic_prompt: str = Field(alias="semanticPrompt")
    camera_motion_effect: str = Field(alias="cameraMotionEffect")
    editing_utility: str = Field(alias="editingUtility")

    model_config = {"populate_by_name": True}


class SourceMaterialOptionalStyleHintsModel(BaseModel):
    style_id: str | None = Field(default=None, alias="styleId")
    storyline_phase_count: int | None = Field(default=None, alias="storylinePhaseCount")
    narrative_goals: list[str] | None = Field(default=None, alias="narrativeGoals")

    model_config = {"populate_by_name": True}


class SourceMaterialModel(BaseModel):
    source_material_id: str = Field(alias="sourceMaterialId")
    source_case_id: str = Field(alias="sourceCaseId")
    duration_ms: int = Field(alias="durationMs")
    bpm: int
    beats_ms: list[int] = Field(default_factory=list, alias="beatsMs")
    drops_ms: list[int] = Field(default_factory=list, alias="dropsMs")
    transcript: SourceMaterialTranscriptModel
    visual_shots: list[SourceMaterialVisualShotModel] = Field(
        default_factory=list, alias="visualShots"
    )
    optional_style_hints: SourceMaterialOptionalStyleHintsModel | None = Field(
        default=None, alias="optionalStyleHints"
    )

    model_config = {"populate_by_name": True}


class TimelinePlanClipModel(BaseModel):
    clip_id: str = Field(alias="clipId")
    asset_id: str | None = Field(default=None, alias="assetId")
    source_material_id: str | None = Field(default=None, alias="sourceMaterialId")
    type: Literal["video", "subtitle", "overlay", "audio"]
    start_ms: int = Field(alias="startMs")
    duration_ms: int = Field(alias="durationMs")
    source_start_ms: int | None = Field(default=None, alias="sourceStartMs")
    label: str
    phase_id: str | None = Field(default=None, alias="phaseId")

    model_config = {"populate_by_name": True}


class TimelinePlanTrackModel(BaseModel):
    track_id: str = Field(alias="trackId")
    type: Literal["video", "subtitle", "overlay", "audio"]
    clips: list[TimelinePlanClipModel] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class TimelinePlanModel(BaseModel):
    timeline_id: str = Field(alias="timelineId")
    workspace_id: str = Field(alias="workspaceId")
    style_id: str = Field(alias="styleId")
    source_asset_ids: list[str] = Field(default_factory=list, alias="sourceAssetIds")
    source_material_ids: list[str] = Field(default_factory=list, alias="sourceMaterialIds")
    target_duration_ms: int = Field(alias="targetDurationMs")
    tracks: list[TimelinePlanTrackModel] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class RenderHintsModel(BaseModel):
    fps: int
    width: int
    height: int
    format: Literal["mp4"]


class EditingJobModel(BaseModel):
    job_id: str = Field(alias="jobId")
    timeline_id: str = Field(alias="timelineId")
    renderer: Literal["hyperframes"]
    status: Literal["draft", "queued", "rendering", "completed", "failed"]
    composition_path: str = Field(alias="compositionPath")
    output_path: str = Field(alias="outputPath")
    render_hints: RenderHintsModel = Field(alias="renderHints")

    model_config = {"populate_by_name": True}


class RenderResultModel(BaseModel):
    render_id: str = Field(alias="renderId")
    job_id: str = Field(alias="jobId")
    status: Literal["not_started", "queued", "rendering", "completed", "failed"]
    output_path: str = Field(alias="outputPath")
    preview_asset_id: str | None = Field(default=None, alias="previewAssetId")
    error_message: str | None = Field(default=None, alias="errorMessage")

    model_config = {"populate_by_name": True}


class EditorExportPackageModel(BaseModel):
    exported_at: str = Field(alias="exportedAt")
    source_assets: list[AssetItemModel] = Field(default_factory=list, alias="sourceAssets")
    source_materials: list[SourceMaterialModel] = Field(default_factory=list, alias="sourceMaterials")
    editing_experience: EditingExperienceModel = Field(alias="editingExperience")
    timeline_plan: TimelinePlanModel = Field(alias="timelinePlan")
    editing_job: EditingJobModel = Field(alias="editingJob")
    render_result: RenderResultModel = Field(alias="renderResult")

    model_config = {"populate_by_name": True}


class HyperFramesSceneModel(BaseModel):
    scene_id: str = Field(alias="sceneId")
    asset_id: str = Field(alias="assetId")
    source_material_id: str = Field(alias="sourceMaterialId")
    asset_name: str = Field(alias="assetName")
    asset_object_url: str | None = Field(default=None, alias="assetObjectUrl")
    timeline_start_ms: int = Field(alias="timelineStartMs")
    duration_ms: int = Field(alias="durationMs")
    source_start_ms: int = Field(alias="sourceStartMs")
    label: str
    subtitle_texts: list[str] = Field(default_factory=list, alias="subtitleTexts")
    overlay_texts: list[str] = Field(default_factory=list, alias="overlayTexts")
    audio_cue_labels: list[str] = Field(default_factory=list, alias="audioCueLabels")

    model_config = {"populate_by_name": True}


class HyperFramesCompositionDraftModel(BaseModel):
    composition_id: str = Field(alias="compositionId")
    timeline_id: str = Field(alias="timelineId")
    renderer: Literal["hyperframes"]
    duration_ms: int = Field(alias="durationMs")
    fps: int
    width: int
    height: int
    total_frames: int = Field(alias="totalFrames")
    scenes: list[HyperFramesSceneModel] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
