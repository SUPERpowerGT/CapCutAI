"""步骤3（合并）: 认知对齐与弹性映射 —— Qwen3-Omni 语义推断 + Python 确定性数学换算。

设计原则（来自规范）:
  - LLM 只负责语义判断（叙事阶段划分、风格标签、转场策略、音效建议等）
  - 所有数值字段（absolute_trigger_ms、relative_beat_offset、时间比例）由 Python 精确计算
  - LLM 输出叙事阶段的时间边界（start_ms/end_ms），Python 按时间重叠为每个镜头分配阶段
  - LLM 可自主定义 PHASE_* 阶段名，不再固定为四段式
  - 当 wav_path 提供时，先用已加载的 Omni 做分块 ASR，再做认知对齐，节省一次模型加载开销
  - 输出须通过 pipeline.schema.validate 校验
"""

from __future__ import annotations

import gc
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pipeline.audio_processor import AudioFeatures
from pipeline.schema import validate
from pipeline.text_processor import TranscriptResult, align_transcript_to_shots
from pipeline.visual_processor import VisualAnalysis


# ---- 提示词构建 ----

def _build_prompt(
    audio: AudioFeatures,
    transcript: TranscriptResult,
    visual: VisualAnalysis,
    shot_alignment: dict[int, dict] | None = None,
) -> str:
    """构建 Omni 认知对齐 prompt。

    shot_alignment: align_transcript_to_shots() 的返回值，key=shot.index，
      value={"aligned_text": str, "sentence_count": int}。
      提供时，每个镜头条目后附带对应口播文字，让 Omni 在推理阶段感知
      「每个画面里说了什么」，大幅提升叙事阶段划分的准确性。
    """
    total_ms = audio.duration_ms
    n = len(visual.shots)

    # 构建镜头列表（含时间戳、景别、情绪、剪辑用途、口播对齐文本）
    shots_lines_parts = []
    for s in visual.shots:
        line = (
            f"  [{s.index}] {s.start_ms}~{s.end_ms}ms | {s.shot_type} | {s.content_type} | "
            f"{s.emotional_tone} | {s.editing_utility} | {s.b_roll_semantic_prompt[:35]}"
        )
        if shot_alignment:
            aligned = shot_alignment.get(s.index, {})
            text = aligned.get("aligned_text", "")
            if text:
                line += f"\n    └ 口播: {text[:80]}"
            else:
                line += "\n    └ 口播: （无）"
        shots_lines_parts.append(line)
    shots_lines = "\n".join(shots_lines_parts)

    # 全局口播文本（句级或全文模式）
    has_alignment = bool(shot_alignment and any(
        v.get("aligned_text") for v in shot_alignment.values()
    ))
    if has_alignment:
        # 已提供对齐数据，全局口播部分作为汇总
        total_text = transcript.full_text[:300] if transcript.full_text else "（无）"
        transcript_text = (
            f"  （已按镜头时间戳对齐，见分镜列表中「口播」字段）\n"
            f"  全文预览: {total_text}"
        )
    elif transcript.sentences:
        transcript_text = "\n".join(
            f"  [{s.start_ms}~{s.end_ms}ms] {s.text[:50]}" for s in transcript.sentences
        )
    else:
        transcript_text = f"  （无句级时间戳）全文: {transcript.full_text[:200]}"

    # 节拍信息（前20个节拍供参考）
    beats_preview = audio.beats_ms[:20]
    beats_str = str(beats_preview) + ("..." if len(audio.beats_ms) > 20 else "")

    # 高潮点作为自然分段参考
    drops_hint = (
        f"  高潮能量爆发点（drops_ms）：{audio.drops_ms}  ← 可作为叙事阶段自然分界参考"
        if audio.drops_ms else "  （未检测到高潮点）"
    )

    # 构建镜头索引列表供 per_shot_annotations 使用
    shot_indices_str = ", ".join(str(s.index) for s in visual.shots)

    return f"""你是一名专业的 AI 视频剪辑师和多模态内容分析专家。
请基于以下视频多模态感知数据，完成视频叙事结构的高层语义抽象。

## 视频基本信息
- 总时长: {total_ms}ms（{total_ms / 1000:.1f}秒）
- BPM: {audio.bpm:.1f}
- 节拍时间点（前20个，ms）: {beats_str}
- 高潮能量点（ms）: {audio.drops_ms}
{drops_hint}

## 口播转录
{transcript_text}

## 视觉分镜（共{n}个镜头，格式：[索引] 时间范围 | 景别 | 内容类型 | 情绪基调 | 剪辑用途 | 画面描述）
{shots_lines}

## 叙事阶段定义规则

大模型需根据视频实际内容，自主规划 2~4 个叙事阶段。阶段命名规范：
- 全大写，以 PHASE_ 为前缀，例如 PHASE_HOOK、PHASE_INTRO 等
- 不同视频类型推荐命名范例（仅供参考，可根据实际内容灵活调整）：
  * 营销口播/知识分享型：PHASE_HOOK → PHASE_PROBLEM → PHASE_SOLUTION → PHASE_CTA
  * 影视混剪/高燃卡点型：PHASE_INTRO → PHASE_BUILDUP → PHASE_CLIMAX → PHASE_OUTRO
  * 生活记录/Vlog型：PHASE_OPENING → PHASE_STORY → PHASE_HIGHLIGHT → PHASE_ENDING
  * 短片/采访型：PHASE_SETUP → PHASE_CORE → PHASE_WRAP

energy_level 能量等级说明：
- HOOK/INTRO/OPENING 类阶段通常为 HIGH（开场抓眼球）
- PROBLEM/BUILDUP/STORY 类阶段通常为 MEDIUM（叙事铺垫）
- SOLUTION/CLIMAX/HIGHLIGHT 类阶段通常为 HIGH 或 PEAK（高潮/解决）
- CTA/OUTRO/ENDING/WRAP 类阶段通常为 MEDIUM 或 LOW（收尾引导）

driving_mode 判断：
- TEXT_LOGIC_DRIVEN：以口播/字幕驱动叙事，画面服务于文案（口播类、知识类、采访类）
- AUDIO_VISUAL_EMOTION：以画面节奏和音乐情绪驱动，无明显口播逻辑线（混剪类、卡点类）

## 转场与音效参考

每个镜头的转场类型（transition_type）：
- 硬切：两镜头直接切换，无过渡（快节奏常用）
- 叠化：两镜头交叉溶解过渡（情感过渡）
- 淡入淡出：镜头从/到黑暗（阶段开始/结束）
- 缩放推进：镜头以缩放动效切换（强调/高能）
- 旋转切换：旋转式转场（创意类）

每个镜头的音效（audio_sfx_type）：
- NONE：无额外音效（平稳段落）
- WHOOSH：划过声（快切/镜头切换）
- POP：弹出声（重点词/字幕弹出）
- SWOOSH：扫过声（转场强调）

bgm_volume_behavior（BGM音量行为）：
- DUCKING：BGM 压低，为人声/重要内容让路
- NORMAL：BGM 保持正常响度

## 输出要求

请严格输出如下 JSON，不要添加任何额外说明：

```json
{{
  "style_metadata": {{
    "style_id": "<kebab-case唯一ID，如: knowledge-vlog-fast-paced>",
    "category": "<核心品类，如: Knowledge_Vlog、Product_Showcase、Life_Record、Movie_Montage>",
    "driving_mode": "<TEXT_LOGIC_DRIVEN|AUDIO_VISUAL_EMOTION>",
    "pacing_style": "<HIGH_CONTRAST_FAST|STEADY_NARRATIVE|EMOTIONAL_SLOW>",
    "visual_theme": "<视觉主题，如: Minimalist_White、Dark_Cinematic、Vibrant_Color、Natural_Outdoor>",
    "tags": ["<标签1>", "<标签2>", "<标签3>"]
  }},
  "storyline_phases": [
    {{
      "phase_id": "<PHASE_HOOK等，全大写PHASE_前缀，根据视频类型自主决定>",
      "energy_level": "<LOW|MEDIUM|HIGH|PEAK>",
      "start_ms": <该阶段起始时间（毫秒整数），第一个阶段必须为0>,
      "end_ms": <该阶段结束时间（毫秒整数），最后一个阶段必须为{total_ms}>,
      "narrative_goal": "<该阶段的导演意图、情绪设计与叙事目标（中文，40字以内）>",
      "bgm_alignment_rule": "<ALIGN_TO_BGM_START|ALIGN_TO_FIRST_DROP|ALIGN_TO_SECOND_DROP|ALIGN_TO_THIRD_DROP|ALIGN_TO_FADE_OUT>"
    }}
  ],
  "visual_assets_rule": {{
    "main_caption": {{
      "font_family_type": "<Sans-Serif-Bold|Serif-Elegant|Handwritten|Monospace>",
      "css_style": "<CSS样式字符串，包含font-size、color、font-weight等>",
      "position_y_percentage": <0-100的数字，表示字幕垂直位置百分比>,
      "highlight_strategy": "<关键词高亮规则描述，如：核心词使用黄色#FFD700加粗>"
    }},
    "global_overlays": []
  }},
  "per_shot_annotations": [
    {{
      "shot_index": <镜头索引，与上方分镜列表对应>,
      "transition_type": "<硬切|叠化|淡入淡出|缩放推进|旋转切换>",
      "transition_duration_beats": <0.25|0.5|1.0，转场持续节拍数>,
      "audio_sfx_type": "<NONE|WHOOSH|POP|SWOOSH>",
      "bgm_volume_behavior": "<NORMAL|DUCKING>"
    }}
  ]
}}
```

约束（必须严格遵守）：
1. storyline_phases 必须包含 2~4 个阶段，按时间先后顺序排列
2. 第一个阶段的 start_ms 必须为 0，最后一个阶段的 end_ms 必须为 {total_ms}
3. 相邻阶段首尾相接，不得有时间空洞或重叠
4. 每个阶段的时间跨度必须与其叙事内容相匹配，像书的章节目录，有清晰边界和叙事转折
5. per_shot_annotations 必须为全部 {n} 个镜头提供注释（索引：{shot_indices_str}）
6. 根据镜头情绪、内容类型和叙事位置判断转场类型和音效，不要机械套用"""


# ---- LLM 推理 ----

def _run_omni_inference(
    model: Any,
    processor: Any,
    video_path: str | Path | None,
    prompt: str,
    max_new_tokens: int,
) -> str:
    """调用 Qwen3-Omni 做推理。video_path 为 None 时使用纯文本模式。"""
    import torch
    from qwen_omni_utils import process_mm_info

    use_audio = False
    if video_path is not None:
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a professional video editing analyst."}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "video", "video": str(Path(video_path).resolve()), "fps": 0.5},
                    {"type": "text", "text": prompt},
                ],
            },
        ]
        use_audio = False
    else:
        messages = [
            {"role": "system", "content": [{"type": "text", "text": "你是专业AI视频剪辑师和内容结构分析专家。"}]},
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
        ]

    text = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
    audios, images, videos = process_mm_info(messages, use_audio_in_video=use_audio)

    inputs = processor(
        text=text,
        audio=audios,
        images=images,
        videos=videos,
        return_tensors="pt",
        padding=True,
        use_audio_in_video=use_audio,
    ).to(model.device).to(model.dtype)

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            thinker_return_dict_in_generate=True,
            use_audio_in_video=use_audio,
            return_audio=False,
        )

    text_ids = outputs[0] if isinstance(outputs, tuple) else outputs
    sequences = text_ids.sequences if hasattr(text_ids, "sequences") else text_ids
    in_len = inputs["input_ids"].shape[1]
    return processor.batch_decode(sequences[:, in_len:], skip_special_tokens=True)[0]


# ---- JSON 解析 ----

def _extract_json(text: str) -> dict:
    """从 LLM 输出中提取 JSON 对象。支持截断修复。"""
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            return _repair_truncated_json(m.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start == -1:
        raise ValueError("无法从模型输出中提取 JSON")

    candidate = text[start: end + 1] if end > start else text[start:]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return _repair_truncated_json(candidate)


def _repair_truncated_json(text: str) -> dict:
    """尝试从截断的 JSON 字符串中提取尽可能多的有效内容。"""
    for i in range(len(text), 0, -1):
        candidate = text[:i].rstrip().rstrip(",")
        open_braces = candidate.count("{") - candidate.count("}")
        open_brackets = candidate.count("[") - candidate.count("]")
        candidate += "]" * max(0, open_brackets) + "}" * max(0, open_braces)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("无法修复截断的 JSON")


# ---- 确定性数学换算 ----

def _get_phase_for_shot(shot_start_ms: int, phases: list[dict]) -> str:
    """按时间重叠确定性地为镜头分配叙事阶段（不依赖 LLM 的 shot_indices）。"""
    for p in phases:
        if p["start_ms"] <= shot_start_ms < p["end_ms"]:
            return p["phase_id"]
    # 兜底：归属最后一个阶段
    return phases[-1]["phase_id"] if phases else "PHASE_HOOK"


def _normalize_phase_boundaries(phases: list[dict], total_ms: int) -> list[dict]:
    """确保阶段首尾相接且覆盖完整视频时长（修正 LLM 可能的边界误差）。"""
    if not phases:
        return phases
    phases = sorted(phases, key=lambda p: p["start_ms"])
    phases[0]["start_ms"] = 0
    for i in range(1, len(phases)):
        phases[i]["start_ms"] = phases[i - 1]["end_ms"]
    phases[-1]["end_ms"] = total_ms
    return phases


_TRANSITION_DEFAULTS = {
    "HOOK_OPENER": ("硬切", 0.25),
    "EMPHASIS_HIGHLIGHT": ("缩放推进", 0.5),
    "TRANSITION_BRIDGE": ("叠化", 1.0),
    "NARRATIVE_SUPPORT": ("硬切", 0.5),
}

_SFX_DEFAULTS = {
    "HIGH_ENERGY": ("WHOOSH", "NORMAL"),
    "PEAK": ("WHOOSH", "NORMAL"),
    "NEUTRAL": ("NONE", "DUCKING"),   # 人声段落 BGM 压低
    "CALM": ("NONE", "NORMAL"),
}


def _assemble_final_json(
    audio: AudioFeatures,
    visual: VisualAnalysis,
    llm_output: dict,
) -> dict:
    """将 LLM 的语义输出与 Python 计算的数值字段合并为最终 Schema。

    核心设计：
    - LLM 输出叙事阶段的时间边界（start_ms/end_ms）和 per_shot_annotations
    - Python 按镜头 start_ms 落在哪个阶段时间范围内，确定性地分配 phase
    - 所有时间比例、beat_offset 均由 Python 精确计算
    - transition_effect / audio_sfx 优先使用 LLM 的 per_shot_annotations，缺失时按规则推断
    """
    total_ms = audio.duration_ms

    # ---- storyline_structure ----
    storyline_phases_raw = llm_output.get("storyline_phases", [])
    storyline_phases_raw = _normalize_phase_boundaries(storyline_phases_raw, total_ms)

    storyline: list[dict] = []
    phase_start_ms_map: dict[str, int] = {}

    for phase_cfg in storyline_phases_raw:
        phase_id: str = phase_cfg.get("phase_id", "PHASE_HOOK")
        start_ms: int = int(phase_cfg.get("start_ms", 0))
        end_ms: int = int(phase_cfg.get("end_ms", total_ms))
        duration_ms = end_ms - start_ms
        phase_start_ms_map[phase_id] = start_ms

        storyline.append({
            "phase_id": phase_id,
            "energy_level": phase_cfg.get("energy_level", "MEDIUM"),
            "narrative_goal": phase_cfg.get("narrative_goal", ""),
            "bgm_alignment_rule": phase_cfg.get("bgm_alignment_rule", "ALIGN_TO_BGM_START"),
            "absolute_time_range": {
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": duration_ms,
            },
            "relative_time_range": {
                "start_ratio": round(start_ms / total_ms, 4),
                "end_ratio": round(end_ms / total_ms, 4),
                "duration_ratio": round(duration_ms / total_ms, 4),
            },
        })

    default_phase = storyline[0]["phase_id"] if storyline else "PHASE_HOOK"

    # 建立 per_shot_annotations 查找表（shot_index → annotations）
    per_shot_map: dict[int, dict] = {}
    for ann in llm_output.get("per_shot_annotations", []):
        idx = ann.get("shot_index")
        if idx is not None:
            per_shot_map[int(idx)] = ann

    # ---- dynamic_pacing_blueprint ----
    blueprint: list[dict] = []
    for shot in visual.shots:
        # 时间重叠分配（确定性，不依赖 LLM）
        phase_id = _get_phase_for_shot(shot.start_ms, storyline_phases_raw) if storyline_phases_raw else default_phase
        phase_start = phase_start_ms_map.get(phase_id, 0)
        trigger_ms = shot.start_ms

        # 从阶段起点到 trigger 之间有多少个节拍（确定性计数）
        relative_beat_offset = sum(
            1 for b in audio.beats_ms if phase_start <= b <= trigger_ms
        )

        # 转场：优先 LLM 注释，缺失则按剪辑用途推断
        ann = per_shot_map.get(shot.index, {})
        trans_type_llm = ann.get("transition_type")
        trans_beats_llm = ann.get("transition_duration_beats")
        if trans_type_llm:
            trans_type = trans_type_llm
            trans_beats = float(trans_beats_llm) if trans_beats_llm is not None else 0.5
        else:
            default_trans, default_beats = _TRANSITION_DEFAULTS.get(
                shot.editing_utility, ("硬切", 0.5)
            )
            trans_type = default_trans
            trans_beats = default_beats

        # 音效：优先 LLM 注释，缺失则按情绪基调推断
        sfx_type_llm = ann.get("audio_sfx_type")
        bgm_beh_llm = ann.get("bgm_volume_behavior")
        if sfx_type_llm:
            sfx_type = sfx_type_llm
            bgm_behavior = bgm_beh_llm or "NORMAL"
        else:
            default_sfx, default_bgm = _SFX_DEFAULTS.get(shot.emotional_tone, ("NONE", "NORMAL"))
            sfx_type = default_sfx
            bgm_behavior = default_bgm

        blueprint.append({
            "belong_to_phase": phase_id,
            "absolute_trigger_ms": trigger_ms,
            "relative_beat_offset": relative_beat_offset,
            "shot_config": {
                "shot_type": shot.shot_type,
                "content_type": shot.content_type,
                "emotional_tone": shot.emotional_tone,
                "b_roll_semantic_prompt": shot.b_roll_semantic_prompt,
                "camera_motion_effect": shot.camera_motion_effect,
                "editing_utility": shot.editing_utility,
            },
            "transition_effect": {
                "type": trans_type,
                "duration_beats": trans_beats,
            },
            "audio_sfx": {
                "trigger_sfx_type": sfx_type,
                "bgm_volume_behavior": bgm_behavior,
            },
        })

    # ---- visual_assets_rule ----
    # 优先级：LLM 输出 > 视觉处理器聚合的字幕信息 > 硬编码兜底
    visual_assets = llm_output.get("visual_assets_rule", {})
    if visual.caption_info and not visual_assets.get("main_caption"):
        visual_assets["main_caption"] = visual.caption_info
    if not visual_assets.get("main_caption"):
        visual_assets["main_caption"] = {
            "font_family_type": "Sans-Serif-Bold",
            "css_style": "font-size: 32px; color: #FFFFFF; font-weight: bold;",
            "position_y_percentage": 75.0,
            "highlight_strategy": "关键词使用高对比度颜色高亮",
        }
    visual_assets.setdefault("global_overlays", [])

    # ---- style_metadata ----
    style_meta = llm_output.get("style_metadata", {})
    style_meta["sample_video_total_duration_ms"] = total_ms
    style_meta.setdefault("style_id", "video-template-01")
    style_meta.setdefault("category", "General")
    style_meta.setdefault("driving_mode", "TEXT_LOGIC_DRIVEN")
    style_meta.setdefault("pacing_style", "STEADY_NARRATIVE")
    style_meta.setdefault("visual_theme", "Minimalist_White")
    style_meta.setdefault("tags", [])

    return {
        "style_metadata": style_meta,
        "storyline_structure": storyline,
        "visual_assets_rule": visual_assets,
        "dynamic_pacing_blueprint": blueprint,
    }


# ---- 主入口 ----

def run_orchestration(
    model_path: str,
    video_path: str | Path,
    audio: AudioFeatures,
    transcript: TranscriptResult | None,
    visual: VisualAnalysis,
    use_video: bool = False,
    wav_path: str | Path | None = None,
    max_new_tokens: int = 4096,
    attn_implementation: str = "flash_attention_2",
) -> tuple[dict, TranscriptResult | None]:
    """加载 Qwen3-Omni，合并原子层数据，输出通过 Schema 校验的弹性 JSON。

    当 wav_path 提供且 transcript 为 None 时，在同一个模型实例上先做分块 ASR
    再做认知对齐，节省一次模型加载开销（约 30-60s）。

    返回值：(final_json, asr_transcript)
    - asr_transcript 在非合并模式下为 None
    """
    import soundfile as sf

    print(f"[Orchestrator] 加载 Omni 模型: {model_path}")
    from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor

    model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
        model_path,
        dtype="auto",
        device_map="auto",
        attn_implementation=attn_implementation,
    )
    processor = Qwen3OmniMoeProcessor.from_pretrained(model_path)

    # ---- Phase A: 合并 ASR（wav_path 提供时）----
    asr_transcript: TranscriptResult | None = None
    if wav_path is not None and transcript is None:
        from pipeline.text_processor import transcribe_with_loaded_omni

        wav_path = Path(wav_path)
        print(f"[Orchestrator] Phase A: 分块 ASR (共享 Omni 实例) ← {wav_path.name}")
        audio_array, sr = sf.read(str(wav_path), dtype="float32", always_2d=False)
        if audio_array.ndim > 1:
            audio_array = audio_array.mean(axis=1)
        asr_transcript = transcribe_with_loaded_omni(model, processor, audio_array)
        print(f"[Orchestrator] ASR 完成: {len(asr_transcript.sentences)} 句，{len(asr_transcript.full_text)} 字")

    effective_transcript = asr_transcript if asr_transcript is not None else transcript
    if effective_transcript is None:
        effective_transcript = TranscriptResult(full_text="", sentences=[])

    # ---- Phase A.5: ASR-VL 时间戳对齐 ----
    # 将 ASR 句子按时间重叠映射到每个 VL 镜头，让 Omni 推理时能感知「每个画面说了什么」
    shot_alignment: dict[int, dict] | None = None
    if effective_transcript.sentences and visual.shots:
        print(f"[Orchestrator] Phase A.5: ASR-VL 时间戳对齐 ({len(effective_transcript.sentences)}句 × {len(visual.shots)}镜)...")
        shot_alignment = align_transcript_to_shots(effective_transcript, visual.shots)
        aligned_count = sum(1 for v in shot_alignment.values() if v.get("aligned_text"))
        print(f"[Orchestrator] 对齐完成: {aligned_count}/{len(visual.shots)} 个镜头有口播文本")
        # 打印前3个对齐结果预览
        for shot in visual.shots[:3]:
            info = shot_alignment.get(shot.index, {})
            txt = info.get("aligned_text", "")
            if txt:
                print(f"  镜头[{shot.index}] {shot.start_ms}~{shot.end_ms}ms → {txt[:40]}")

    # ---- Phase B: 认知对齐推理 ----
    print("[Orchestrator] Phase B: 认知对齐推理（含口播-镜头对齐上下文）...")
    prompt = _build_prompt(audio, effective_transcript, visual, shot_alignment=shot_alignment)
    vid = Path(video_path) if use_video else None
    response = _run_omni_inference(model, processor, vid, prompt, max_new_tokens)

    del model, processor
    gc.collect()
    import torch as _torch
    _torch.cuda.empty_cache()

    print("[Orchestrator] 解析 LLM 输出...")
    try:
        llm_output = _extract_json(response)
    except (ValueError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Omni 输出 JSON 解析失败: {e}\n原始输出:\n{response[:500]}") from e

    print("[Orchestrator] 执行确定性数学换算...")
    final_json = _assemble_final_json(audio, visual, llm_output)

    print("[Orchestrator] Schema 校验...")
    validate(final_json)

    return final_json, asr_transcript
