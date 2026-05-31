"""GLM-ASR-Nano-2512 独立测试脚本。

测试内容：
  1. 全文转录（直接输入完整 WAV 路径）
  2. 长音频分块转录（近似句级时间戳）—— GLM-ASR 不内置时间戳，以 chunk 边界近似
  3. 结果与 Whisper 对齐分析

用法：
  python run_glm_asr_test.py
"""

from __future__ import annotations

import gc
import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from transformers import AutoProcessor, GlmAsrForConditionalGeneration

# ---- 配置 ----
MODEL_PATH = "models/asr/GLM-ASR-Nano-2512"
VIDEO_PATH = Path("data/283851334-1-208.mp4")
OUTPUT_DIR = Path("outputs/glm_asr_test")
WAV_PATH   = OUTPUT_DIR / "test_audio.wav"

# 分块时长：30 秒一块（便于近似句级时间戳，且单块不会太长导致截断）
CHUNK_SEC     = 30
MAX_NEW_TOKENS = 500
SAMPLE_RATE   = 16000


# ================================================================
# 工具函数
# ================================================================

def load_model():
    print(f"[GLM-ASR] 加载处理器: {MODEL_PATH}")
    processor = AutoProcessor.from_pretrained(MODEL_PATH)
    print(f"[GLM-ASR] 加载模型: {MODEL_PATH}")
    t0 = time.time()
    model = GlmAsrForConditionalGeneration.from_pretrained(
        MODEL_PATH,
        dtype="auto",
        device_map="auto",
    )
    print(f"[GLM-ASR] 模型加载完成，耗时 {time.time() - t0:.1f}s")
    print(f"[GLM-ASR] 模型设备: {model.device}, dtype: {model.dtype}")
    return processor, model


def transcribe_file(processor, model, wav_path: Path) -> str:
    """直接用文件路径转录（官方推荐方式）。"""
    print(f"\n[Test-1] 全文转录（直接传文件路径）...")
    t0 = time.time()
    inputs = processor.apply_transcription_request(str(wav_path))
    inputs = inputs.to(model.device, dtype=model.dtype)
    outputs = model.generate(**inputs, do_sample=False, max_new_tokens=MAX_NEW_TOKENS)
    decoded = processor.batch_decode(
        outputs[:, inputs.input_ids.shape[1]:],
        skip_special_tokens=True,
    )
    elapsed = time.time() - t0
    text = decoded[0] if decoded else ""
    print(f"[Test-1] 耗时 {elapsed:.1f}s，识别长度 {len(text)} 字")
    return text


def transcribe_array(processor, model, audio_array: np.ndarray) -> str:
    """用 numpy 数组转录（验证数组输入路径）。"""
    inputs = processor.apply_transcription_request(audio_array)
    inputs = inputs.to(model.device, dtype=model.dtype)
    outputs = model.generate(**inputs, do_sample=False, max_new_tokens=MAX_NEW_TOKENS)
    decoded = processor.batch_decode(
        outputs[:, inputs.input_ids.shape[1]:],
        skip_special_tokens=True,
    )
    return decoded[0] if decoded else ""


def transcribe_chunked(
    processor,
    model,
    audio_array: np.ndarray,
    chunk_sec: int = CHUNK_SEC,
) -> list[dict]:
    """
    将音频切分为固定时长 chunk，逐段转录。
    返回近似句级时间戳（以 chunk 边界为起止时间）。

    注意：GLM-ASR 不支持内置时间戳，此处以 chunk 边界作为近似时间区间。
    实际句子可能跨越 chunk 边界，但对于口播类短视频误差在可接受范围内。
    """
    total_sec = len(audio_array) / SAMPLE_RATE
    chunk_samples = chunk_sec * SAMPLE_RATE
    n_chunks = int(np.ceil(total_sec / chunk_sec))
    print(f"\n[Test-2] 分块转录：总时长 {total_sec:.1f}s，{chunk_sec}s/块，共 {n_chunks} 块")

    segments = []
    for i in range(n_chunks):
        start_sample = i * chunk_samples
        end_sample   = min((i + 1) * chunk_samples, len(audio_array))
        chunk        = audio_array[start_sample:end_sample]
        start_sec    = i * chunk_sec
        end_sec      = end_sample / SAMPLE_RATE

        t0 = time.time()
        text = transcribe_array(processor, model, chunk)
        elapsed = time.time() - t0

        seg = {
            "chunk_index": i,
            "start_ms":    int(start_sec * 1000),
            "end_ms":      int(end_sec * 1000),
            "start_sec":   round(start_sec, 3),
            "end_sec":     round(end_sec, 3),
            "duration_sec": round(end_sec - start_sec, 3),
            "text":        text.strip(),
            "inference_sec": round(elapsed, 2),
        }
        segments.append(seg)
        print(f"  块 {i + 1}/{n_chunks} [{start_sec:.0f}s~{end_sec:.0f}s] "
              f"({elapsed:.1f}s) → {text[:60]}{'...' if len(text) > 60 else ''}")

    return segments


def check_model_info(processor, model):
    """打印模型基本信息供参考。"""
    print("\n[Info] 模型参数量:", sum(p.numel() for p in model.parameters()) / 1e6, "M")
    print("[Info] 特征提取器采样率:", processor.feature_extractor.sampling_rate)
    try:
        print("[Info] 分词器词汇量:", processor.tokenizer.vocab_size)
    except Exception:
        pass


# ================================================================
# 主流程
# ================================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 确认音频存在
    if not WAV_PATH.exists():
        print(f"[Error] WAV 不存在，请先提取: {WAV_PATH}")
        return

    # 读取音频数组（备用：直接传路径更简洁，但测试两种方式）
    print(f"[Load] 读取 WAV: {WAV_PATH}")
    audio_array, sr = sf.read(str(WAV_PATH), dtype="float32", always_2d=False)
    print(f"[Load] 采样率={sr} Hz, 时长={len(audio_array)/sr:.1f}s, 形状={audio_array.shape}")
    if sr != SAMPLE_RATE:
        import librosa
        audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=SAMPLE_RATE)

    # 加载模型
    processor, model = load_model()
    check_model_info(processor, model)

    results = {}

    # ---- Test 1: 全文转录（文件路径输入）----
    t_start = time.time()
    full_text_from_path = transcribe_file(processor, model, WAV_PATH)
    results["test1_full_text_from_path"] = {
        "method":   "apply_transcription_request(file_path)",
        "text":     full_text_from_path,
        "char_count": len(full_text_from_path),
        "total_sec":  round(time.time() - t_start, 2),
    }

    # ---- Test 2: 分块转录（numpy 数组输入，获取近似时间戳）----
    t_start = time.time()
    segments = transcribe_chunked(processor, model, audio_array, chunk_sec=CHUNK_SEC)
    full_text_chunked = "".join(s["text"] for s in segments)
    results["test2_chunked_with_approx_timestamps"] = {
        "method":        f"chunked transcription ({CHUNK_SEC}s/chunk, numpy array input)",
        "note":          "GLM-ASR 不支持内置时间戳；时间区间为 chunk 边界（近似值），实际句子可能跨 chunk",
        "segments":      segments,
        "full_text":     full_text_chunked,
        "char_count":    len(full_text_chunked),
        "segment_count": len(segments),
        "total_sec":     round(time.time() - t_start, 2),
    }

    # ---- 差异分析 ----
    print("\n[分析] 两种方式字数对比:")
    print(f"  方式1（完整路径）: {len(full_text_from_path)} 字")
    print(f"  方式2（分块拼接）: {len(full_text_chunked)} 字")
    if len(full_text_from_path) < len(full_text_chunked) * 0.8:
        print("  ⚠ 完整路径方式字数明显少于分块方式 → 可能存在长音频截断问题")
        print(f"     完整路径截断率: {1 - len(full_text_from_path)/max(1, len(full_text_chunked)):.1%}")
    else:
        print("  ✓ 两种方式字数接近，无明显截断")

    results["summary"] = {
        "model":       MODEL_PATH,
        "video":       str(VIDEO_PATH),
        "audio_duration_sec": round(len(audio_array) / SAMPLE_RATE, 1),
        "test1_char_count": len(full_text_from_path),
        "test2_char_count": len(full_text_chunked),
        "truncation_detected": len(full_text_from_path) < len(full_text_chunked) * 0.8,
        "timestamp_support": "native: NO; approximated via chunk boundaries: YES",
    }

    # 保存结果
    output_file = OUTPUT_DIR / "glm_asr_result.json"
    output_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[完成] 结果已保存: {output_file}")
    print(f"[完成] 全文（方式2拼接）前200字: {full_text_chunked[:200]}")

    del model, processor
    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
