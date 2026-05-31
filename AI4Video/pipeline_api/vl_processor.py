"""步骤2（API版）: 视觉分镜分析 —— 镜头检测 + Qwen3-VL API 逐帧语义标注。

与本地版的区别仅在于「单帧推理」由本地 GPU 推理换成 API 调用。
镜头边界检测（像素差算法）和关键帧提取（PyAV）保持本地执行，无需模型。

复用的本地组件：
  - pipeline.visual_processor.detect_shot_boundaries  （纯算法，无模型）
  - pipeline.visual_processor._SHOT_ANALYSIS_PROMPT   （统一 prompt 模板）
  - pipeline.visual_processor._parse_shot_json        （JSON 解析 + 默认值）
  - pipeline.visual_processor._aggregate_caption_info （字幕样式聚合）
  - pipeline.visual_processor.ShotAnalysis / VisualAnalysis（数据结构）
  - framework.frame_extractor.VideoFrameExtractor      （PyAV 关键帧提取）
"""

from __future__ import annotations

import base64
from pathlib import Path

from pipeline.visual_processor import (
    ShotAnalysis,
    VisualAnalysis,
    _SHOT_ANALYSIS_PROMPT,
    _aggregate_caption_info,
    _parse_shot_json,
    detect_shot_boundaries,
)
from pipeline_api.client import chat_completion
from pipeline_api.config import API_KEYS, MAX_TOKENS, MODELS


# ── 图像编码 ──────────────────────────────────────────────────────────────────

def _encode_image_b64(image_path: Path) -> str:
    """将本地 JPEG/PNG 关键帧编码为 base64 data URI，供 image_url 字段使用。"""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    suffix = image_path.suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
    return f"data:image/{mime};base64,{data}"


# ── 单帧 API 分析 ─────────────────────────────────────────────────────────────

def _analyze_keyframe_api(image_path: Path) -> dict:
    """调用 Qwen3-VL API 对单张关键帧进行结构化语义分析。

    消息格式遵循 OpenAI image_url 规范，302.ai 与官方格式一致。
    解析失败时返回安全默认值（与本地版行为一致）。
    """
    if not image_path.exists():
        return _parse_shot_json("")

    image_uri = _encode_image_b64(image_path)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": image_uri},
                },
                {
                    "type": "text",
                    "text": _SHOT_ANALYSIS_PROMPT,
                },
            ],
        }
    ]

    try:
        response = chat_completion(
            messages=messages,
            model=MODELS["vl"],
            api_key=API_KEYS["vl"],
            max_tokens=MAX_TOKENS["vl_shot"],
        )
        return _parse_shot_json(response)
    except Exception as e:
        print(f"[VL-API] 关键帧分析异常（{type(e).__name__}: {e}），使用默认值")
        return _parse_shot_json("")


# ── 主入口 ────────────────────────────────────────────────────────────────────

def run_visual_analysis_api(
    video_path: str | Path,
    keyframes_dir: str | Path,
    max_shots: int = 30,
    analyze_all: bool = False,
    diff_threshold: float = 0.25,
) -> VisualAnalysis:
    """镜头检测（本地算法）+ Qwen3-VL API 逐帧分析。

    与本地版 run_visual_analysis() 接口完全一致，返回相同的 VisualAnalysis 对象。

    Args:
        video_path:      输入视频路径。
        keyframes_dir:   关键帧 JPEG 的输出目录。
        max_shots:       最大分析镜头数（超出则均匀采样）。
        analyze_all:     True 时跳过采样上限，分析所有镜头。
        diff_threshold:  像素差镜头检测阈值（0~1）。
    """
    from framework.frame_extractor import VideoFrameExtractor

    video_path = Path(video_path)
    keyframes_dir = Path(keyframes_dir)
    keyframes_dir.mkdir(parents=True, exist_ok=True)

    # 1. 镜头边界检测（纯算法，复用本地实现）
    print("[VL-API] 镜头边界检测中...")
    boundaries = detect_shot_boundaries(video_path, diff_threshold=diff_threshold)
    shot_intervals = [
        (boundaries[i], boundaries[i + 1]) for i in range(len(boundaries) - 1)
    ]
    print(f"[VL-API] 检测到 {len(shot_intervals)} 个镜头")

    if not analyze_all and len(shot_intervals) > max_shots:
        step = len(shot_intervals) / max_shots
        indices = [int(i * step) for i in range(max_shots)]
        shot_intervals = [shot_intervals[i] for i in indices]
        print(f"[VL-API] 采样至 {max_shots} 个镜头进行分析（全量分析请使用 analyze_all=True）")
    elif analyze_all:
        print(f"[VL-API] 全量分析模式：对全部 {len(shot_intervals)} 个镜头逐一分析")

    # 2. 关键帧提取（PyAV，取每镜头时间中点）
    print("[VL-API] 关键帧提取中...")
    keyframe_paths: list[Path] = []
    shot_start_end: list[tuple[int, int]] = []

    with VideoFrameExtractor(video_path) as ext:
        for i, (start_sec, end_sec) in enumerate(shot_intervals):
            mid_sec = (start_sec + end_sec) / 2.0
            kf_path = keyframes_dir / f"shot_{i:03d}_{int(start_sec * 1000)}ms.jpg"
            try:
                ext.extract_frame(mid_sec, kf_path)
            except RuntimeError:
                pass  # 提取失败时保留路径占位，后续跳过
            keyframe_paths.append(kf_path)
            shot_start_end.append((int(start_sec * 1000), int(end_sec * 1000)))

    # 3. Qwen3-VL API 逐帧语义分析
    shots: list[ShotAnalysis] = []
    shots_raw: list[dict] = []
    total = len(keyframe_paths)

    for i, (kf_path, (start_ms, end_ms)) in enumerate(
        zip(keyframe_paths, shot_start_end)
    ):
        print(f"[VL-API] 分析镜头 {i + 1}/{total} ...")
        raw = _analyze_keyframe_api(kf_path)
        shots_raw.append(raw)
        shots.append(
            ShotAnalysis(
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
            )
        )

    caption_info = _aggregate_caption_info(shots_raw)
    print(f"[VL-API] 视觉分析完成: {len(shots)} 个镜头")
    return VisualAnalysis(shots=shots, caption_info=caption_info)
