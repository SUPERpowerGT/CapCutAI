import audioCaseA from "../../../../../data/test_case/7c8980565c6eb03ecfc916cef2c3671d/step1_audio.json";
import transcriptCaseA from "../../../../../data/test_case/7c8980565c6eb03ecfc916cef2c3671d/step2_transcript.json";
import visualCaseA from "../../../../../data/test_case/7c8980565c6eb03ecfc916cef2c3671d/step3_visual.json";
import styleHintCaseA from "../../../../../data/test_case/7c8980565c6eb03ecfc916cef2c3671d/elastic_template.json";

import audioCaseB from "../../../../../data/test_case/27daab568829a31941b9eb1a0ce6502d/step1_audio.json";
import transcriptCaseB from "../../../../../data/test_case/27daab568829a31941b9eb1a0ce6502d/step2_transcript.json";
import visualCaseB from "../../../../../data/test_case/27daab568829a31941b9eb1a0ce6502d/step3_visual.json";
import styleHintCaseB from "../../../../../data/test_case/27daab568829a31941b9eb1a0ce6502d/elastic_template.json";

import audioCaseC from "../../../../../data/test_case/3b5ffa605eee8e7e5ace9365a48386d7/step1_audio.json";
import transcriptCaseC from "../../../../../data/test_case/3b5ffa605eee8e7e5ace9365a48386d7/step2_transcript.json";
import visualCaseC from "../../../../../data/test_case/3b5ffa605eee8e7e5ace9365a48386d7/step3_visual.json";
import styleHintCaseC from "../../../../../data/test_case/3b5ffa605eee8e7e5ace9365a48386d7/elastic_template.json";

import audioCaseD from "../../../../../data/test_case/69ead07c5604ccf49e0ef54177553003/step1_audio.json";
import transcriptCaseD from "../../../../../data/test_case/69ead07c5604ccf49e0ef54177553003/step2_transcript.json";
import visualCaseD from "../../../../../data/test_case/69ead07c5604ccf49e0ef54177553003/step3_visual.json";
import styleHintCaseD from "../../../../../data/test_case/69ead07c5604ccf49e0ef54177553003/elastic_template.json";

import type {SourceMaterial} from "../types/editor-preview";

type AudioStep = {
  bpm?: number;
  beats_ms?: number[];
  drops_ms?: number[];
  duration_ms?: number;
};

type TranscriptStep = {
  full_text?: string;
  sentences?: Array<{
    text?: string;
    start_ms?: number;
    end_ms?: number;
  }>;
};

type VisualStep = {
  shots?: Array<{
    index?: number;
    start_ms?: number;
    end_ms?: number;
    shot_type?: string;
    content_type?: string;
    emotional_tone?: string;
    b_roll_semantic_prompt?: string;
    camera_motion_effect?: string;
    editing_utility?: string;
  }>;
};

type OptionalStyleHints = {
  style_metadata?: {
    style_id?: string;
  };
  storyline_structure?: Array<{
    narrative_goal?: string;
  }>;
};

function buildSourceMaterialFromCase({
  caseId,
  audio,
  transcript,
  visual,
  styleHints
}: {
  caseId: string;
  audio: AudioStep;
  transcript: TranscriptStep;
  visual: VisualStep;
  styleHints: OptionalStyleHints;
}): SourceMaterial {
  return {
    sourceMaterialId: `source_material_${caseId}`,
    sourceCaseId: caseId,
    durationMs: audio.duration_ms ?? 0,
    bpm: audio.bpm ?? 0,
    beatsMs: audio.beats_ms ?? [],
    dropsMs: audio.drops_ms ?? [],
    transcript: {
      fullText: transcript.full_text ?? "",
      sentences: (transcript.sentences ?? []).map((sentence) => ({
        text: sentence.text ?? "",
        startMs: sentence.start_ms ?? 0,
        endMs: sentence.end_ms ?? 0
      }))
    },
    visualShots: (visual.shots ?? []).map((shot) => ({
      index: shot.index ?? 0,
      startMs: shot.start_ms ?? 0,
      endMs: shot.end_ms ?? 0,
      shotType: shot.shot_type ?? "UNKNOWN",
      contentType: shot.content_type ?? "UNKNOWN",
      emotionalTone: shot.emotional_tone ?? "UNKNOWN",
      semanticPrompt: shot.b_roll_semantic_prompt ?? "",
      cameraMotionEffect: shot.camera_motion_effect ?? "UNKNOWN",
      editingUtility: shot.editing_utility ?? "UNKNOWN"
    })),
    optionalStyleHints: {
      styleId: styleHints.style_metadata?.style_id,
      storylinePhaseCount: styleHints.storyline_structure?.length ?? 0,
      narrativeGoals: (styleHints.storyline_structure ?? [])
        .map((phase) => phase.narrative_goal ?? "")
        .filter(Boolean)
    }
  };
}

const mockSourceMaterialPool: SourceMaterial[] = [
  buildSourceMaterialFromCase({
    caseId: "7c8980565c6eb03ecfc916cef2c3671d",
    audio: audioCaseA as AudioStep,
    transcript: transcriptCaseA as TranscriptStep,
    visual: visualCaseA as VisualStep,
    styleHints: styleHintCaseA as OptionalStyleHints
  }),
  buildSourceMaterialFromCase({
    caseId: "27daab568829a31941b9eb1a0ce6502d",
    audio: audioCaseB as AudioStep,
    transcript: transcriptCaseB as TranscriptStep,
    visual: visualCaseB as VisualStep,
    styleHints: styleHintCaseB as OptionalStyleHints
  }),
  buildSourceMaterialFromCase({
    caseId: "3b5ffa605eee8e7e5ace9365a48386d7",
    audio: audioCaseC as AudioStep,
    transcript: transcriptCaseC as TranscriptStep,
    visual: visualCaseC as VisualStep,
    styleHints: styleHintCaseC as OptionalStyleHints
  }),
  buildSourceMaterialFromCase({
    caseId: "69ead07c5604ccf49e0ef54177553003",
    audio: audioCaseD as AudioStep,
    transcript: transcriptCaseD as TranscriptStep,
    visual: visualCaseD as VisualStep,
    styleHints: styleHintCaseD as OptionalStyleHints
  })
];

export function loadMockSourceMaterialPool() {
  return mockSourceMaterialPool;
}

export function selectMockSourceMaterials(assetCount: number) {
  if (assetCount <= 0) {
    return mockSourceMaterialPool.slice(0, 1);
  }

  return mockSourceMaterialPool.slice(0, Math.min(assetCount, mockSourceMaterialPool.length));
}
