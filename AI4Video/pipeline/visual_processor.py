"""步骤3: 视觉处理 —— 镜头检测 + Qwen3-VL 逐镜语义分析。

流程：
  1. 像素差（Pixel-Difference）镜头检测 → 获取镜头边界时间列表
  2. 每个镜头截取中点关键帧（PyAV）
  3. Qwen3-VL 对每帧做图像理解，提取语义信息
"""

from __future__ import annotations

import gc
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---- 数据结构 ----

@dataclass
class ShotAnalysis:
    index: int
    start_ms: int
    end_ms: int
    keyframe_path: str
    shot_type: str               # A_ROLL_CLOSE_UP | A_ROLL_MEDIUM | B_ROLL_SEMANTIC
    content_type: str            # PRESENTER | PRODUCT | SCENE | TEXT_GRAPHIC
    emotional_tone: str          # HIGH_ENERGY | NEUTRAL | CALM
    b_roll_semantic_prompt: str  # 纯视觉语义，用于向量检索
    camera_motion_effect: str
    editing_utility: str         # HOOK_OPENER | NARRATIVE_SUPPORT | EMPHASIS_HIGHLIGHT | TRANSITION_BRIDGE


@dataclass
class VisualAnalysis:
    shots: list[ShotAnalysis]
    caption_info: dict | None = None  # 从各镜头聚合的字幕样式信息


# ---- 镜头检测 ----

def detect_shot_boundaries(
    video_path: Path,
    diff_threshold: float = 0.25,
    stride: int = 3,
    min_shot_sec: float = 0.5,
) -> list[float]:
    """基于像素差的镜头边界检测，返回包含 0.0 和视频总时长的时间点列表（秒）。

    stride: 每隔 stride 帧检测一次，降低计算量。
    diff_threshold: 相邻帧平均绝对差超过此值即判定为镜头切换（0~1 范围）。
    min_shot_sec: 同一镜头的最短时长，防止连续误检。
    """
    import av
    import numpy as np

    boundaries = [0.0]
    prev = None
    frame_idx = 0
    duration_sec = 0.0

    with av.open(str(video_path)) as container:
        stream = next(s for s in container.streams if s.type == "video")
        if stream.duration and stream.time_base:
            duration_sec = float(stream.duration * stream.time_base)
        elif container.duration:
            duration_sec = float(container.duration) / 1_000_000

        for frame in container.decode(stream):
            if frame_idx % stride != 0:
                frame_idx += 1
                continue

            ts = float(frame.pts * frame.time_base) if frame.pts is not None else 0.0

            # 降采样到灰度小图，减少计算量
            arr = frame.to_ndarray(format="gray")[::8, ::8].astype(np.float32) / 255.0

            if prev is not None:
                diff = float(np.mean(np.abs(arr - prev)))
                if diff > diff_threshold and (ts - boundaries[-1]) >= min_shot_sec:
                    boundaries.append(ts)

            prev = arr
            frame_idx += 1

    boundaries.append(max(duration_sec, boundaries[-1] + min_shot_sec))
    return boundaries


# ---- VL 单帧分析 ----

_SHOT_ANALYSIS_PROMPT = """你是一名专业AI视频剪辑师，正在分析一帧视频截图以提取结构化剪辑元数据。

请严格按以下 JSON 格式输出，不要添加任何额外文字：

{
  "shot_type": "A_ROLL_CLOSE_UP 或 A_ROLL_MEDIUM 或 B_ROLL_SEMANTIC",
  "content_type": "PRESENTER（出镜讲解） 或 PRODUCT（产品展示） 或 SCENE（环境/场景） 或 TEXT_GRAPHIC（文字/图形）",
  "emotional_tone": "HIGH_ENERGY（高能/激昂） 或 NEUTRAL（平稳叙述） 或 CALM（舒缓/情感）",
  "b_roll_semantic_prompt": "画面视觉内容的详细中文描述，50字以内，聚焦主体、色彩、构图，不描述字幕文字，用于素材向量检索",
  "camera_motion_effect": "静态 或 轻微放大 或 轻微缩小 或 左移 或 右移 或 震动",
  "editing_utility": "HOOK_OPENER（适合开头吸引眼球） 或 NARRATIVE_SUPPORT（叙事辅助） 或 EMPHASIS_HIGHLIGHT（强调关键点） 或 TRANSITION_BRIDGE（转场过渡）",
  "has_caption": true或false,
  "caption_position_y_pct": 如有明显字幕则为0到100的整数（0=顶部，100=底部），否则填null,
  "caption_css_hint": "如有字幕则简述字体大小和颜色风格（如：36px白色加粗无衬线字体），否则填null",
  "caption_font_family": "如有字幕则填 Sans-Serif-Bold（无衬线加粗）或 Serif-Elegant（衬线雅致）或 Handwritten（手写风）或 Monospace（等宽/代码风），否则填null",
  "caption_highlight_style": "如有字幕且存在关键词高亮（如黄色字、描边、背景色块），则描述高亮方式（例如：核心词使用黄色#FFD700加粗高亮），否则填null"
}

景别选择规则：
- A_ROLL_CLOSE_UP：人物面部特写或半身特写（肩部以上）
- A_ROLL_MEDIUM：人物中景（腰部或全身可见）
- B_ROLL_SEMANTIC：无主要人物，或以产品/场景/环境为主体"""


def _infer_single_image(
    model: Any,
    processor: Any,
    image_path: Path,
    max_new_tokens: int = 384,
) -> dict:
    """用 Qwen3-VL 分析单张关键帧，返回解析后的字典（解析失败返回默认值）。"""
    import torch
    from qwen_vl_utils import process_vision_info

    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": f"file://{image_path.resolve()}"},
            {"type": "text", "text": _SHOT_ANALYSIS_PROMPT},
        ],
    }]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, _, _ = process_vision_info(messages, return_video_kwargs=True)

    inputs = processor(
        text=[text],
        images=image_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)

    with torch.inference_mode():
        generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens, repetition_penalty=1.05)

    trimmed = generated_ids[0][inputs.input_ids.shape[1]:]
    response = processor.decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)

    return _parse_shot_json(response)


def _parse_shot_json(text: str) -> dict:
    """从 VL 响应中提取 JSON，解析失败时返回安全默认值。"""
    default = {
        "shot_type": "B_ROLL_SEMANTIC",
        "content_type": "SCENE",
        "emotional_tone": "NEUTRAL",
        "b_roll_semantic_prompt": "画面内容待分析",
        "camera_motion_effect": "静态",
        "editing_utility": "NARRATIVE_SUPPORT",
        "has_caption": False,
        "caption_position_y_pct": None,
        "caption_css_hint": None,
        "caption_font_family": None,
        "caption_highlight_style": None,
    }
    try:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            data = json.loads(m.group())
            valid_shot_types = {"A_ROLL_CLOSE_UP", "A_ROLL_MEDIUM", "B_ROLL_SEMANTIC"}
            valid_content_types = {"PRESENTER", "PRODUCT", "SCENE", "TEXT_GRAPHIC"}
            valid_tones = {"HIGH_ENERGY", "NEUTRAL", "CALM"}
            valid_editing_utilities = {
                "HOOK_OPENER",
                "NARRATIVE_SUPPORT",
                "EMPHASIS_HIGHLIGHT",
                "TRANSITION_BRIDGE",
            }

            data["shot_type"] = _normalize_enum_value(
                data.get("shot_type"), valid_shot_types
            )
            data["content_type"] = _normalize_enum_value(
                data.get("content_type"), valid_content_types
            )
            data["emotional_tone"] = _normalize_enum_value(
                data.get("emotional_tone"), valid_tones
            )
            data["editing_utility"] = _normalize_enum_value(
                data.get("editing_utility"), valid_editing_utilities
            )

            if data.get("shot_type") not in valid_shot_types:
                data["shot_type"] = "B_ROLL_SEMANTIC"
            if data.get("content_type") not in valid_content_types:
                data["content_type"] = "SCENE"
            if data.get("emotional_tone") not in valid_tones:
                data["emotional_tone"] = "NEUTRAL"
            if data.get("editing_utility") not in valid_editing_utilities:
                data["editing_utility"] = "NARRATIVE_SUPPORT"
            return {**default, **data}
    except (json.JSONDecodeError, TypeError):
        pass
    return default


def _normalize_enum_value(value: Any, valid_values: set[str]) -> Any:
    """清洗模型输出的枚举值，容忍尾随说明文字或轻微格式噪声。"""
    if not isinstance(value, str):
        return value

    trimmed = value.strip()
    if trimmed in valid_values:
        return trimmed

    # 常见情况：`HOOK_OPENER（适合开头吸引眼球）`
    prefix = re.split(r"[（(]", trimmed, maxsplit=1)[0].strip()
    if prefix in valid_values:
        return prefix

    # 兜底：从字符串中提取第一个合法枚举 token
    for candidate in sorted(valid_values, key=len, reverse=True):
        if candidate in trimmed:
            return candidate

    return value


# ---- 字幕信息聚合 ----

def _aggregate_caption_info(shots_raw: list[dict]) -> dict | None:
    """从各镜头的字幕检测结果聚合出全局字幕样式。无字幕镜头则返回 None。"""
    import numpy as np

    captioned = [s for s in shots_raw if s.get("has_caption")]
    if not captioned:
        return None

    y_values = [s["caption_position_y_pct"] for s in captioned if s.get("caption_position_y_pct") is not None]
    position_y = float(np.median(y_values)) if y_values else 75.0

    css_hints = [s["caption_css_hint"] for s in captioned if s.get("caption_css_hint")]
    css_style = css_hints[0] if css_hints else "font-size: 32px; color: #FFFFFF; font-weight: bold;"

    # 从 VL 检测结果中投票选出最常见的字体族（有检测值时使用，否则从 css_hint 推断）
    font_votes = [s["caption_font_family"] for s in captioned if s.get("caption_font_family")]
    if font_votes:
        font_family_type = max(set(font_votes), key=font_votes.count)
    elif css_style and "bold" in css_style.lower():
        font_family_type = "Sans-Serif-Bold"
    else:
        font_family_type = "Sans-Serif-Bold"

    # 高亮风格：取第一个有描述的检测值，没有则使用通用描述
    highlight_votes = [s["caption_highlight_style"] for s in captioned if s.get("caption_highlight_style")]
    highlight_strategy = highlight_votes[0] if highlight_votes else "关键词使用高对比度颜色高亮"

    return {
        "font_family_type": font_family_type,
        "css_style": css_style,
        "position_y_percentage": round(position_y, 1),
        "highlight_strategy": highlight_strategy,
    }


# ---- 主入口 ----

def run_visual_analysis(
    model_path: str,
    video_path: str | Path,
    keyframes_dir: str | Path,
    max_shots: int = 30,
    analyze_all: bool = False,
    diff_threshold: float = 0.25,
    attn_implementation: str = "flash_attention_2",
    dtype: str = "bfloat16",
) -> VisualAnalysis:
    """镜头检测 + VL 逐镜分析。

    analyze_all=True 时对所有检测到的镜头逐一分析，忽略 max_shots 限制。
    analyze_all=False（默认）时，超过 max_shots 则均匀采样。
    """
    video_path = Path(video_path)
    keyframes_dir = Path(keyframes_dir)
    keyframes_dir.mkdir(parents=True, exist_ok=True)

    # 1. 镜头检测
    print("[Visual] 镜头边界检测中...")
    boundaries = detect_shot_boundaries(video_path, diff_threshold=diff_threshold)
    shot_intervals = [(boundaries[i], boundaries[i + 1]) for i in range(len(boundaries) - 1)]
    print(f"[Visual] 检测到 {len(shot_intervals)} 个镜头")

    # 若镜头数超限且非全量模式，均匀采样
    if not analyze_all and len(shot_intervals) > max_shots:
        step = len(shot_intervals) / max_shots
        indices = [int(i * step) for i in range(max_shots)]
        shot_intervals = [shot_intervals[i] for i in indices]
        print(f"[Visual] 采样至 {max_shots} 个镜头进行分析（全量分析请使用 analyze_all=True）")
    elif analyze_all:
        print(f"[Visual] 全量分析模式：对全部 {len(shot_intervals)} 个镜头逐一分析")

    # 2. 提取关键帧（取每镜头中点）
    print("[Visual] 关键帧提取中...")
    from framework.frame_extractor import VideoFrameExtractor

    keyframe_paths: list[Path] = []
    shot_start_end: list[tuple[int, int]] = []

    with VideoFrameExtractor(video_path) as ext:
        for i, (start_sec, end_sec) in enumerate(shot_intervals):
            mid_sec = (start_sec + end_sec) / 2.0
            kf_path = keyframes_dir / f"shot_{i:03d}_{int(start_sec * 1000)}ms.jpg"
            try:
                ext.extract_frame(mid_sec, kf_path)
                keyframe_paths.append(kf_path)
            except RuntimeError:
                keyframe_paths.append(kf_path)  # 保留占位，后续跳过
            shot_start_end.append((int(start_sec * 1000), int(end_sec * 1000)))

    # 3. 加载 VL 模型并逐帧分析
    print(f"[Visual] 加载 VL 模型: {model_path}")
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    torch_dtype = getattr(torch, dtype)
    model = AutoModelForImageTextToText.from_pretrained(
        model_path,
        dtype=torch_dtype,
        attn_implementation=attn_implementation,
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(model_path)

    shots: list[ShotAnalysis] = []
    shots_raw: list[dict] = []

    for i, (kf_path, (start_ms, end_ms)) in enumerate(zip(keyframe_paths, shot_start_end)):
        print(f"[Visual] 分析镜头 {i + 1}/{len(keyframe_paths)} ...")
        if not kf_path.exists():
            raw = _parse_shot_json("")  # 使用默认值
        else:
            raw = _infer_single_image(model, processor, kf_path)
        shots_raw.append(raw)

        shots.append(ShotAnalysis(
            index=i,
            start_ms=start_ms,
            end_ms=end_ms,
            keyframe_path=str(kf_path),
            shot_type=raw["shot_type"],
            content_type=raw["content_type"],
            emotional_tone=raw["emotional_tone"],
            b_roll_semantic_prompt=raw["b_roll_semantic_prompt"],
            camera_motion_effect=raw["camera_motion_effect"],
            editing_utility=raw["editing_utility"],
        ))

    del model, processor
    gc.collect()
    torch.cuda.empty_cache()

    caption_info = _aggregate_caption_info(shots_raw)
    return VisualAnalysis(shots=shots, caption_info=caption_info)
