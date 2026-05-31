"""Mock 数据生成器 —— 当模型权重不可用时，返回结构完全一致的仿真数据。

每个函数的返回类型与对应真实处理器的输出类型相同，
mock_final_json() 直接返回通过 Schema 校验的完整 JSON。
"""

from __future__ import annotations

from pathlib import Path

from pipeline.audio_processor import AudioFeatures
from pipeline.text_processor import SentenceTimestamp, TranscriptResult
from pipeline.visual_processor import ShotAnalysis, VisualAnalysis


def mock_audio_features(duration_ms: int = 60_000, bpm: float = 120.0) -> AudioFeatures:
    """生成模拟音频特征。节拍按 BPM 均匀分布，高潮点取 1/4、1/2、3/4 处。"""
    beat_interval_ms = int(60_000 / bpm)
    beats_ms = list(range(0, duration_ms, beat_interval_ms))
    drops_ms = [
        int(duration_ms * 0.25),
        int(duration_ms * 0.5),
        int(duration_ms * 0.75),
    ]
    return AudioFeatures(bpm=bpm, beats_ms=beats_ms, drops_ms=drops_ms, duration_ms=duration_ms)


def mock_transcript(duration_ms: int = 60_000) -> TranscriptResult:
    """生成模拟转录结果，包含 4 个均匀分布的句子时间戳。"""
    quarter = duration_ms // 4
    sentences = [
        SentenceTimestamp("大家好，今天我要分享一个非常实用的技巧。", 0, quarter),
        SentenceTimestamp("你是否遇到过这样的问题？每次都不知道该怎么办。", quarter, quarter * 2),
        SentenceTimestamp("今天我来告诉你最简单有效的解决方案。", quarter * 2, quarter * 3),
        SentenceTimestamp("照着这个方法来，你也可以轻松搞定。快去试试吧！", quarter * 3, duration_ms),
    ]
    full_text = "".join(s.text for s in sentences)
    return TranscriptResult(full_text=full_text, sentences=sentences)


def mock_visual_analysis(duration_ms: int = 60_000, keyframes_dir: Path | None = None) -> VisualAnalysis:
    """生成模拟视觉分析结果，包含 8 个均匀分布的镜头。"""
    n_shots = 8
    shot_ms = duration_ms // n_shots
    kf_dir = keyframes_dir or Path("outputs/pipeline/mock/keyframes")

    shot_types = [
        "A_ROLL_MEDIUM", "A_ROLL_CLOSE_UP", "B_ROLL_SEMANTIC", "A_ROLL_MEDIUM",
        "B_ROLL_SEMANTIC", "A_ROLL_CLOSE_UP", "A_ROLL_MEDIUM", "B_ROLL_SEMANTIC",
    ]
    content_types = [
        "PRESENTER", "PRESENTER", "SCENE", "PRESENTER",
        "PRODUCT", "PRESENTER", "PRESENTER", "TEXT_GRAPHIC",
    ]
    emotional_tones = [
        "HIGH_ENERGY", "NEUTRAL", "NEUTRAL", "NEUTRAL",
        "NEUTRAL", "HIGH_ENERGY", "NEUTRAL", "CALM",
    ]
    b_roll_descs = [
        "主播面对镜头，背景整洁白色书房，神情自信",
        "主播特写面部，眼神坚定，灯光柔和",
        "书桌上的笔记本电脑屏幕显示代码，室内自然光线",
        "主播中景，双手比划讲解，白色背景",
        "产品特写，光滑表面反光，极简白色背景",
        "主播特写，嘴唇动作清晰，面部表情专注",
        "主播微笑，手持产品向镜头展示",
        "品牌Logo特写，白底黑字，干净简洁",
    ]
    camera_motions = ["静态", "轻微放大", "静态", "静态", "轻微缩小", "静态", "静态", "静态"]
    editing_utilities = [
        "HOOK_OPENER", "NARRATIVE_SUPPORT", "NARRATIVE_SUPPORT", "NARRATIVE_SUPPORT",
        "EMPHASIS_HIGHLIGHT", "EMPHASIS_HIGHLIGHT", "NARRATIVE_SUPPORT", "TRANSITION_BRIDGE",
    ]

    shots = [
        ShotAnalysis(
            index=i,
            start_ms=i * shot_ms,
            end_ms=(i + 1) * shot_ms,
            keyframe_path=str(kf_dir / f"shot_{i:03d}_mock.jpg"),
            shot_type=shot_types[i],
            content_type=content_types[i],
            emotional_tone=emotional_tones[i],
            b_roll_semantic_prompt=b_roll_descs[i],
            camera_motion_effect=camera_motions[i],
            editing_utility=editing_utilities[i],
        )
        for i in range(n_shots)
    ]

    caption_info = {
        "font_family_type": "Sans-Serif-Bold",
        "css_style": "font-size: 36px; color: #FFFFFF; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);",
        "position_y_percentage": 78.0,
        "highlight_strategy": "核心关键词使用黄色（#FFD700）高亮显示",
    }
    return VisualAnalysis(shots=shots, caption_info=caption_info)


def mock_final_json(duration_ms: int = 60_000) -> dict:
    """生成通过 Schema 校验的完整弹性模板 JSON。"""
    audio = mock_audio_features(duration_ms)
    visual = mock_visual_analysis(duration_ms)
    n = len(visual.shots)

    def _beats_in_range(start: int, end: int) -> int:
        return sum(1 for b in audio.beats_ms if start <= b <= end)

    phases = [
        ("PHASE_HOOK",     [0, 1],    "ALIGN_TO_BGM_START",   "HIGH",
         "通过主播直视镜头与简洁背景建立信任感，3秒内抓住观众注意力"),
        ("PHASE_PROBLEM",  [2, 3],    "ALIGN_TO_FIRST_DROP",  "MEDIUM",
         "以场景镜头与口播结合的方式呈现痛点，引发观众共鸣"),
        ("PHASE_SOLUTION", [4, 5, 6], "ALIGN_TO_SECOND_DROP", "HIGH",
         "展示解决方案，产品特写与主播讲解交替，强化信任背书"),
        ("PHASE_CTA",      [7],       "ALIGN_TO_FADE_OUT",    "MEDIUM",
         "收尾号召行动，品牌露出配合主播引导完成转化闭环"),
    ]

    storyline = []
    phase_start_map: dict[str, int] = {}
    shot_to_phase: dict[int, str] = {}

    for phase_id, indices, bgm_rule, energy, goal in phases:
        start_ms = visual.shots[indices[0]].start_ms
        end_ms = visual.shots[indices[-1]].end_ms
        dur = end_ms - start_ms
        phase_start_map[phase_id] = start_ms
        for i in indices:
            shot_to_phase[i] = phase_id
        storyline.append({
            "phase_id": phase_id,
            "energy_level": energy,
            "narrative_goal": goal,
            "bgm_alignment_rule": bgm_rule,
            "absolute_time_range": {"start_ms": start_ms, "end_ms": end_ms, "duration_ms": dur},
            "relative_time_range": {
                "start_ratio": round(start_ms / duration_ms, 4),
                "end_ratio": round(end_ms / duration_ms, 4),
                "duration_ratio": round(dur / duration_ms, 4),
            },
        })

    transitions = ["硬切", "硬切", "叠化", "硬切", "淡入淡出", "硬切", "硬切", "淡入淡出"]
    sfx_types = ["NONE", "WHOOSH", "NONE", "WHOOSH", "NONE", "POP", "NONE", "NONE"]
    bgm_behaviors = ["NORMAL", "DUCKING", "NORMAL", "DUCKING", "NORMAL", "DUCKING", "NORMAL", "DUCKING"]

    blueprint = []
    for shot in visual.shots:
        phase_id = shot_to_phase[shot.index]
        phase_start = phase_start_map[phase_id]
        trigger_ms = shot.start_ms
        beat_offset = sum(1 for b in audio.beats_ms if phase_start <= b <= trigger_ms)
        blueprint.append({
            "belong_to_phase": phase_id,
            "absolute_trigger_ms": trigger_ms,
            "relative_beat_offset": beat_offset,
            "shot_config": {
                "shot_type": shot.shot_type,
                "content_type": shot.content_type,
                "emotional_tone": shot.emotional_tone,
                "b_roll_semantic_prompt": shot.b_roll_semantic_prompt,
                "camera_motion_effect": shot.camera_motion_effect,
                "editing_utility": shot.editing_utility,
            },
            "transition_effect": {
                "type": transitions[shot.index],
                "duration_beats": 0.5,
            },
            "audio_sfx": {
                "trigger_sfx_type": sfx_types[shot.index],
                "bgm_volume_behavior": bgm_behaviors[shot.index],
            },
        })

    return {
        "style_metadata": {
            "style_id": "knowledge-vlog-mock-01",
            "category": "Knowledge_Vlog",
            "driving_mode": "TEXT_LOGIC_DRIVEN",
            "pacing_style": "STEADY_NARRATIVE",
            "visual_theme": "Minimalist_White",
            "sample_video_total_duration_ms": duration_ms,
            "tags": ["口播", "知识分享", "极简风格", "产品推荐"],
        },
        "storyline_structure": storyline,
        "visual_assets_rule": {
            "main_caption": {
                "font_family_type": "Sans-Serif-Bold",
                "css_style": "font-size: 36px; color: #FFFFFF; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);",
                "position_y_percentage": 78.0,
                "highlight_strategy": "核心关键词使用黄色（#FFD700）高亮显示",
            },
            "global_overlays": [],
        },
        "dynamic_pacing_blueprint": blueprint,
    }
