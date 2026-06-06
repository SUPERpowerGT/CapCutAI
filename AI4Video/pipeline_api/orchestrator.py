"""步骤4（API版）: 认知对齐与弹性映射 —— Qwen3-Omni API + Python 确定性数学换算。

与本地版的区别仅在于「模型推理」由本地 GPU 推理换成 API 调用。
所有 Prompt 构建、JSON 解析、数学换算逻辑完全复用本地实现。

复用的本地组件：
  - pipeline.orchestrator._build_prompt       （Omni 推理 Prompt 构建）
  - pipeline.orchestrator._extract_json       （LLM 输出 JSON 提取 + 截断修复）
  - pipeline.orchestrator._assemble_final_json（数值字段换算 + Schema 组装）
  - pipeline.schema.validate                  （Schema 校验）
  - pipeline.text_processor.align_transcript_to_shots（ASR-VL 时间戳对齐）
"""

from __future__ import annotations

from typing import Any

from pipeline.audio_processor import AudioFeatures
from pipeline.orchestrator import (
    _assemble_final_json,
    _build_prompt,
    _extract_json,
)
from pipeline.schema import validate
from pipeline.text_processor import TranscriptResult, align_transcript_to_shots
from pipeline.visual_processor import VisualAnalysis
from pipeline_api.client import chat_completion
from pipeline_api.config import API_KEYS, MAX_TOKENS, MODELS


# ── 主入口 ────────────────────────────────────────────────────────────────────

def run_orchestration_api(
    audio: AudioFeatures,
    transcript: TranscriptResult,
    visual: VisualAnalysis,
) -> dict[str, Any]:
    """认知对齐与弹性映射 —— Qwen3-Omni API 版本。

    与本地版 run_orchestration() 核心逻辑一致：
      Phase A.5: ASR-VL 时间戳对齐（口播文本→镜头对齐）
      Phase B:   构建 Prompt + Qwen3-Omni API 推理（叙事阶段 + 转场注释）
      Phase C:   Python 确定性换算（时间比例 / 节拍偏移 / 阶段分配）+ Schema 校验

    Args:
        audio:      步骤1音频特征（BPM / 节拍 / 高潮点）。
        transcript: 步骤2语音转录（全文 + 句级时间戳）。
        visual:     步骤3视觉分析（镜头列表 + 字幕信息）。

    Returns:
        通过 Schema 校验的最终弹性 JSON 字典。
    """
    # Phase A.5: ASR-VL 时间戳对齐
    print("[Orchestrator-API] Phase A.5: ASR-VL 时间戳对齐...")
    shot_alignment = align_transcript_to_shots(transcript, visual.shots)
    aligned_count = sum(1 for v in shot_alignment.values() if v.get("aligned_text"))
    print(f"[Orchestrator-API] {aligned_count}/{len(visual.shots)} 个镜头获得口播对齐文本")

    # Phase B: 构建 Prompt + API 调用
    print("[Orchestrator-API] Phase B: 构建认知对齐 Prompt...")
    prompt = _build_prompt(audio, transcript, visual, shot_alignment)

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    print("[Orchestrator-API] 调用 Qwen3-Omni API 进行认知对齐推理...")
    response = chat_completion(
        messages=messages,
        model=MODELS["omni"],
        api_key=API_KEYS["omni"],
        max_tokens=MAX_TOKENS["orchestrator"],
        temperature=0.1,
    )

    # Phase C: JSON 解析 + 确定性数学换算
    print("[Orchestrator-API] 解析 LLM 输出并组装最终 JSON...")
    llm_output = _extract_json(response)
    final_json = _assemble_final_json(audio, visual, llm_output)

    # Schema 校验
    validate(final_json)
    print("[Orchestrator-API] Schema 校验通过")

    return final_json
