"""弹性视频模板 JSON Schema 定义与校验。"""

from __future__ import annotations

import jsonschema

ELASTIC_VIDEO_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "IndustrialAdaptiveVideoTemplate",
    "type": "object",
    "required": ["style_metadata", "storyline_structure", "visual_assets_rule", "dynamic_pacing_blueprint"],
    "properties": {
        "style_metadata": {
            "type": "object",
            "required": ["style_id", "category", "driving_mode", "pacing_style", "visual_theme", "sample_video_total_duration_ms"],
            "properties": {
                "style_id": {"type": "string"},
                "category": {"type": "string"},
                "driving_mode": {
                    "type": "string",
                    "enum": ["TEXT_LOGIC_DRIVEN", "AUDIO_VISUAL_EMOTION"],
                    "description": "核心驱动模式：TEXT_LOGIC_DRIVEN(文本逻辑驱动)；AUDIO_VISUAL_EMOTION(视听情绪驱动)",
                },
                "pacing_style": {"type": "string", "enum": ["HIGH_CONTRAST_FAST", "STEADY_NARRATIVE", "EMOTIONAL_SLOW"]},
                "visual_theme": {"type": "string"},
                "sample_video_total_duration_ms": {"type": "integer"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        },
        "storyline_structure": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["phase_id", "energy_level", "narrative_goal", "bgm_alignment_rule", "absolute_time_range", "relative_time_range"],
                "properties": {
                    "phase_id": {
                        "type": "string",
                        "pattern": "^PHASE_[A-Z][A-Z0-9_]*$",
                        "description": "由LLM自主定义的叙事/节奏阶段ID，必须全大写并以PHASE_为前缀",
                    },
                    "energy_level": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "PEAK"],
                        "description": "该阶段的情绪/视听能量等级",
                    },
                    "narrative_goal": {"type": "string"},
                    "bgm_alignment_rule": {
                        "type": "string",
                        "enum": ["ALIGN_TO_BGM_START", "ALIGN_TO_FIRST_DROP", "ALIGN_TO_SECOND_DROP", "ALIGN_TO_THIRD_DROP", "ALIGN_TO_FADE_OUT"],
                    },
                    "absolute_time_range": {
                        "type": "object",
                        "required": ["start_ms", "end_ms", "duration_ms"],
                        "properties": {
                            "start_ms": {"type": "integer"},
                            "end_ms": {"type": "integer"},
                            "duration_ms": {"type": "integer"},
                        },
                    },
                    "relative_time_range": {
                        "type": "object",
                        "required": ["start_ratio", "end_ratio", "duration_ratio"],
                        "properties": {
                            "start_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                            "end_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                            "duration_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                    },
                },
            },
        },
        "visual_assets_rule": {
            "type": "object",
            "required": ["main_caption", "global_overlays"],
            "properties": {
                "main_caption": {
                    "type": "object",
                    "required": ["font_family_type", "css_style", "position_y_percentage", "highlight_strategy"],
                    "properties": {
                        "font_family_type": {"type": "string"},
                        "css_style": {"type": "string"},
                        "position_y_percentage": {"type": "number"},
                        "highlight_strategy": {"type": "string"},
                    },
                },
                "global_overlays": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["layer_type", "css_class_definition"],
                        "properties": {
                            "layer_type": {
                                "type": "string",
                                "enum": ["TOP_PROGRESS_BAR", "BACKGROUND_NOISE_MASK", "WATERMARK_HINT", "FRAME_BORDER"],
                            },
                            "css_class_definition": {"type": "string"},
                        },
                    },
                },
            },
        },
        "dynamic_pacing_blueprint": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["belong_to_phase", "absolute_trigger_ms", "relative_beat_offset", "shot_config", "transition_effect", "audio_sfx"],
                "properties": {
                    "belong_to_phase": {
                        "type": "string",
                        "pattern": "^PHASE_[A-Z][A-Z0-9_]*$",
                        "description": "与 storyline_structure 中 phase_id 完全一致",
                    },
                    "absolute_trigger_ms": {"type": "integer"},
                    "relative_beat_offset": {"type": "integer"},
                    "shot_config": {
                        "type": "object",
                        "required": ["shot_type", "b_roll_semantic_prompt", "camera_motion_effect"],
                        "properties": {
                            "shot_type": {
                                "type": "string",
                                "enum": ["A_ROLL_CLOSE_UP", "A_ROLL_MEDIUM", "B_ROLL_SEMANTIC"],
                            },
                            "content_type": {
                                "type": "string",
                                "enum": ["PRESENTER", "PRODUCT", "SCENE", "TEXT_GRAPHIC"],
                            },
                            "emotional_tone": {
                                "type": "string",
                                "enum": ["HIGH_ENERGY", "NEUTRAL", "CALM"],
                            },
                            "b_roll_semantic_prompt": {"type": "string"},
                            "camera_motion_effect": {"type": "string"},
                            "editing_utility": {
                                "type": "string",
                                "enum": ["HOOK_OPENER", "NARRATIVE_SUPPORT", "EMPHASIS_HIGHLIGHT", "TRANSITION_BRIDGE"],
                            },
                        },
                    },
                    "transition_effect": {
                        "type": "object",
                        "required": ["type", "duration_beats"],
                        "properties": {
                            "type": {"type": "string"},
                            "duration_beats": {"type": "number"},
                        },
                    },
                    "audio_sfx": {
                        "type": "object",
                        "required": ["trigger_sfx_type", "bgm_volume_behavior"],
                        "properties": {
                            "trigger_sfx_type": {"type": "string"},
                            "bgm_volume_behavior": {"type": "string", "enum": ["DUCKING", "NORMAL"]},
                        },
                    },
                },
            },
        },
    },
}


def validate(data: dict) -> None:
    """校验数据是否符合弹性视频模板 Schema。不合格则抛出 jsonschema.ValidationError。"""
    jsonschema.validate(instance=data, schema=ELASTIC_VIDEO_SCHEMA)
