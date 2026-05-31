import elasticTemplate from "../../../../../data/elastic_template.json";
import type {EditingExperience} from "../types/editor-preview";

type ElasticTemplate = {
  style_metadata?: {
    style_id?: string;
    category?: string;
    pacing_style?: string;
    visual_theme?: string;
    tags?: string[];
    sample_video_total_duration_ms?: number;
  };
  storyline_structure?: Array<{
    phase_id?: string;
    narrative_goal?: string;
    absolute_time_range?: {
      start_ms?: number;
      end_ms?: number;
      duration_ms?: number;
    };
  }>;
  dynamic_pacing_blueprint?: unknown[];
};

const template = elasticTemplate as ElasticTemplate;

export function loadMockEditingExperience(): EditingExperience {
  const metadata = template.style_metadata ?? {};
  const styleId = metadata.style_id ?? "mock-style";

  return {
    experienceId: `mock_${styleId}`,
    styleId,
    category: metadata.category ?? "UNKNOWN",
    styleName: styleId
      .split("-")
      .filter(Boolean)
      .map((part) => part.slice(0, 1).toUpperCase() + part.slice(1))
      .join(" "),
    pacingStyle: metadata.pacing_style ?? "UNKNOWN",
    visualTheme: metadata.visual_theme ?? "UNKNOWN",
    tags: metadata.tags ?? [],
    sampleVideoDurationMs: metadata.sample_video_total_duration_ms ?? 0,
    storylinePhases: (template.storyline_structure ?? []).map((phase) => ({
      phaseId: phase.phase_id ?? "PHASE_UNKNOWN",
      narrativeGoal: phase.narrative_goal ?? "",
      startMs: phase.absolute_time_range?.start_ms ?? 0,
      endMs: phase.absolute_time_range?.end_ms ?? 0,
      durationMs: phase.absolute_time_range?.duration_ms ?? 0
    })),
    dynamicBeatCount: template.dynamic_pacing_blueprint?.length ?? 0
  };
}
