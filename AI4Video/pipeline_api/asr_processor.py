"""步骤2（API版）: 语音识别 —— 分块音频 + Qwen3-Omni API ASR。

与本地版的区别仅在于「模型推理」由本地 GPU 推理换成 API 调用。
音频提取（PyAV）和分块逻辑保持与本地版完全一致。

复用的本地组件：
  - pipeline.text_processor.SentenceTimestamp / TranscriptResult（数据结构）
  - pipeline.text_processor._ASR_OMNI_PROMPT                   （统一 prompt 模板）
  - pipeline.text_processor._parse_omni_asr_response           （JSON 解析 + 时间偏移）
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from pipeline.text_processor import (
    SentenceTimestamp,
    TranscriptResult,
    _ASR_OMNI_PROMPT,
    _parse_omni_asr_response,
)
from pipeline_api.client import chat_completion
from pipeline_api.config import API_KEYS, ASR_CHUNK_SEC, ASR_SAMPLE_RATE, MAX_TOKENS, MODELS


# ── 音频编码 ──────────────────────────────────────────────────────────────────

def _encode_audio_b64(audio_array: np.ndarray, sample_rate: int) -> str:
    """将 numpy 音频数组编码为 base64 WAV data URI，供 audio_url 字段使用。"""
    # Use a temp file to avoid cffi virtual IO callbacks on hardened macOS.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        sf.write(tmp.name, audio_array, sample_rate, format="WAV", subtype="PCM_16")
        tmp.seek(0)
        data = base64.b64encode(tmp.read()).decode("utf-8")
    return f"data:audio/wav;base64,{data}"


# ── 单块 API ASR ──────────────────────────────────────────────────────────────

def _transcribe_chunk_api(
    chunk_arr: np.ndarray,
    chunk_start_sec: float,
    language: str,
) -> list[SentenceTimestamp]:
    """调用 Qwen3-Omni API 对单个音频块进行 ASR，返回含绝对时间偏移的句级时间戳。"""
    audio_uri = _encode_audio_b64(chunk_arr, ASR_SAMPLE_RATE)
    prompt = f"{_ASR_OMNI_PROMPT}\n\n语言提示：{language}"
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "audio_url",
                    "audio_url": {"url": audio_uri},
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        }
    ]

    try:
        response = chat_completion(
            messages=messages,
            model=MODELS["omni"],
            api_key=API_KEYS["omni"],
            max_tokens=MAX_TOKENS["asr_chunk"],
        )
        return _parse_omni_asr_response(response, offset_sec=chunk_start_sec)
    except Exception as e:
        print(f"[ASR-API] 块转录异常（offset={chunk_start_sec:.1f}s, {type(e).__name__}: {e}），跳过此块")
        return []


# ── 主入口 ────────────────────────────────────────────────────────────────────

def run_asr_api(
    wav_path: str | Path,
    language: str = "Chinese",
) -> TranscriptResult:
    """分块音频 ASR —— Qwen3-Omni API 版本。

    将音频切为 ASR_CHUNK_SEC（60s）一块，每块独立调用 API，
    再按时间偏移合并为完整转录。与本地版 run_asr_with_omni() 接口一致。

    Args:
        wav_path:  16kHz 单声道 WAV 文件路径（已由步骤1提取）。
        language:  语言提示（如 Chinese / English / Japanese）。

    Returns:
        TranscriptResult，含 full_text 和句级时间戳列表。
    """
    wav_path = Path(wav_path)
    audio_array, sr = sf.read(str(wav_path), dtype="float32", always_2d=False)

    # 确保单声道 16kHz
    if audio_array.ndim > 1:
        audio_array = audio_array.mean(axis=1)
    if sr != ASR_SAMPLE_RATE:
        import librosa
        audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=ASR_SAMPLE_RATE)

    chunk_samples = ASR_CHUNK_SEC * ASR_SAMPLE_RATE
    total_samples = len(audio_array)
    total_chunks = (total_samples + chunk_samples - 1) // chunk_samples

    print(f"[ASR-API] 音频时长: {total_samples / ASR_SAMPLE_RATE:.1f}s，分 {total_chunks} 块处理")

    all_sentences: list[SentenceTimestamp] = []
    for i in range(total_chunks):
        start = i * chunk_samples
        end = min(start + chunk_samples, total_samples)
        chunk_arr = audio_array[start:end]
        chunk_start_sec = start / ASR_SAMPLE_RATE
        print(f"[ASR-API] 转录块 {i + 1}/{total_chunks}（起始 {chunk_start_sec:.1f}s）...")
        sentences = _transcribe_chunk_api(chunk_arr, chunk_start_sec, language)
        all_sentences.extend(sentences)
        print(f"[ASR-API] 块 {i + 1} 识别出 {len(sentences)} 句")

    full_text = "".join(s.text for s in all_sentences)
    print(f"[ASR-API] ASR 完成: 共 {len(all_sentences)} 句，{len(full_text)} 字")
    return TranscriptResult(full_text=full_text, sentences=all_sentences)
