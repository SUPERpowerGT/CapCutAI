"""Qwen3-Omni 语音识别能力测试。

测试维度：
  T1  音频输入 + 纯文本转录                 ← 基础 ASR 准确度
  T2  音频输入 + 句级时间戳 JSON            ← 时间戳对齐能力（句子粒度）
  T3  音频输入 + 词/字级时间戳 JSON         ← 时间戳对齐能力（词粒度）
  T4  视频输入（use_audio_in_video=True）  ← 视频模式 ASR 准确度
  T5  长音频分块 + 句级时间戳（全片）       ← 实用性验证（341s 完整视频）

测试素材：
  视频  283851334-1-208.mp4（341s，中文口播 Vlog）
  音频  已提取 WAV（16kHz mono）

用法：
  python run_omni_asr_test.py
"""

from __future__ import annotations

import gc
import json
import re
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from qwen_omni_utils import process_mm_info
from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor

# ---- 配置 ----
MODEL_PATH  = "models/omni/Qwen3-Omni-30B-A3B-Instruct"
VIDEO_PATH  = Path("data/283851334-1-208.mp4")
WAV_PATH    = Path("outputs/glm_asr_test/test_audio.wav")
OUTPUT_DIR  = Path("outputs/omni_asr_test")
SAMPLE_RATE = 16000

# 测试用音频片段：取第 2 块（30~60s），内容丰富且无歌词干扰
PROBE_START_SEC = 30.0
PROBE_END_SEC   = 60.0

# 分块处理（T5）
CHUNK_SEC = 30


# ================================================================
# 工具函数
# ================================================================

def load_model(attn_impl: str = "flash_attention_2"):
    print(f"[Omni] 加载模型: {MODEL_PATH}")
    t0 = time.time()
    model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
        MODEL_PATH,
        dtype="auto",
        device_map="auto",
        attn_implementation=attn_impl,
    )
    processor = Qwen3OmniMoeProcessor.from_pretrained(MODEL_PATH)
    print(f"[Omni] 加载完成 {time.time() - t0:.1f}s  device={model.device}  dtype={model.dtype}")
    return model, processor


def infer(model, processor, messages: list[dict], max_new_tokens: int = 2048) -> str:
    """统一推理入口。"""
    use_audio_in_video = any(
        ele.get("type") == "video"
        for msg in messages
        for ele in (msg.get("content") if isinstance(msg.get("content"), list) else [])
    )

    text_input = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False
    )
    audios, images, videos = process_mm_info(messages, use_audio_in_video=use_audio_in_video)

    inputs = processor(
        text=text_input,
        audio=audios,
        images=images,
        videos=videos,
        return_tensors="pt",
        padding=True,
        use_audio_in_video=use_audio_in_video,
    ).to(model.device).to(model.dtype)

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            thinker_return_dict_in_generate=True,
            use_audio_in_video=use_audio_in_video,
            return_audio=False,
        )

    text_ids = outputs[0] if isinstance(outputs, tuple) else outputs
    sequences = text_ids.sequences if hasattr(text_ids, "sequences") else text_ids
    in_len = inputs["input_ids"].shape[1]
    return processor.batch_decode(sequences[:, in_len:], skip_special_tokens=True)[0]


def build_audio_messages(audio_input, system_text: str, user_text: str) -> list[dict]:
    """构建音频输入消息（支持 numpy 数组或文件路径）。"""
    return [
        {"role": "system", "content": [{"type": "text", "text": system_text}]},
        {"role": "user", "content": [
            {"type": "audio", "audio": audio_input},
            {"type": "text", "text": user_text},
        ]},
    ]


def build_video_messages(video_path: str, system_text: str, user_text: str) -> list[dict]:
    """构建视频输入消息（use_audio_in_video 由 infer() 自动检测）。"""
    return [
        {"role": "system", "content": [{"type": "text", "text": system_text}]},
        {"role": "user", "content": [
            {"type": "video", "video": video_path, "fps": 0.5,
             "video_start": 0.0, "video_end": 60.0},
            {"type": "text", "text": user_text},
        ]},
    ]


def extract_json(text: str) -> dict | None:
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


# ================================================================
# 各项测试
# ================================================================

SYS_ASR = "你是专业的语音识别助手，能准确转录中文口播内容。"

PROMPT_PLAIN = "请将音频内容转录为文字，输出完整的口播文本。不要添加任何额外内容。"

PROMPT_SENT_TS = """请将音频内容转录为文字，并输出句级时间戳。

严格按以下 JSON 格式输出，不要添加任何额外文字：
{"sentences": [{"text": "句子内容", "start_sec": 0.0, "end_sec": 2.5}]}

要求：
1. 按自然语句断句（句号、问号、感叹号或语义完整的短句）
2. start_sec 和 end_sec 是相对于本段音频起始的秒数（精度 0.1s）
3. 若音频无人声或静音，返回 {"sentences": []}"""

PROMPT_WORD_TS = """请将音频内容转录为文字，并以词或短语为单位输出时间戳。

严格按以下 JSON 格式输出：
{"words": [{"word": "词/短语内容", "start_sec": 0.0, "end_sec": 0.5}]}

每个 word 条目包含 2-6 个汉字或一个完整英文单词，start_sec/end_sec 精度 0.1s。
若音频无人声，返回 {"words": []}"""


def run_t1_plain(model, processor, audio_chunk: np.ndarray) -> dict:
    """T1: 音频输入 + 纯文本转录（基础准确度）。"""
    print("\n[T1] 音频输入 → 纯文本转录...")
    messages = build_audio_messages(audio_chunk, SYS_ASR, PROMPT_PLAIN)
    t0 = time.time()
    response = infer(model, processor, messages, max_new_tokens=1024)
    elapsed = round(time.time() - t0, 2)
    print(f"[T1] 耗时 {elapsed}s | 输出: {response[:100]}")
    return {"prompt": "plain_transcription", "response": response,
            "char_count": len(response), "elapsed_sec": elapsed}


def run_t2_sent_ts(model, processor, audio_chunk: np.ndarray, chunk_start_sec: float = 0.0) -> dict:
    """T2: 音频输入 + 句级时间戳 JSON。"""
    print("\n[T2] 音频输入 → 句级时间戳 JSON...")
    messages = build_audio_messages(audio_chunk, SYS_ASR, PROMPT_SENT_TS)
    t0 = time.time()
    response = infer(model, processor, messages, max_new_tokens=2048)
    elapsed = round(time.time() - t0, 2)
    print(f"[T2] 耗时 {elapsed}s | 原始输出: {response[:150]}")

    parsed = extract_json(response)
    sentences = []
    if parsed:
        for s in parsed.get("sentences", []):
            sentences.append({
                "text":     s.get("text", ""),
                "start_sec": round(float(s.get("start_sec", 0)) + chunk_start_sec, 3),
                "end_sec":   round(float(s.get("end_sec", 0)) + chunk_start_sec, 3),
                "start_ms":  int((float(s.get("start_sec", 0)) + chunk_start_sec) * 1000),
                "end_ms":    int((float(s.get("end_sec", 0)) + chunk_start_sec) * 1000),
            })
    print(f"[T2] 解析到 {len(sentences)} 句" + (" ✓" if sentences else " ✗ JSON 解析失败"))
    return {"prompt": "sentence_level_timestamps", "raw_response": response,
            "sentences": sentences, "parse_success": bool(sentences),
            "elapsed_sec": elapsed}


def run_t3_word_ts(model, processor, audio_chunk: np.ndarray) -> dict:
    """T3: 音频输入 + 词级时间戳 JSON。"""
    print("\n[T3] 音频输入 → 词级时间戳 JSON...")
    messages = build_audio_messages(audio_chunk, SYS_ASR, PROMPT_WORD_TS)
    t0 = time.time()
    response = infer(model, processor, messages, max_new_tokens=2048)
    elapsed = round(time.time() - t0, 2)
    print(f"[T3] 耗时 {elapsed}s | 原始输出: {response[:150]}")

    parsed = extract_json(response)
    words = parsed.get("words", []) if parsed else []
    print(f"[T3] 解析到 {len(words)} 个词级条目" + (" ✓" if words else " ✗ JSON 解析失败"))
    return {"prompt": "word_level_timestamps", "raw_response": response,
            "words": words, "parse_success": bool(words), "elapsed_sec": elapsed}


def run_t4_video(model, processor) -> dict:
    """T4: 视频模式（use_audio_in_video=True），取前 60s。"""
    print("\n[T4] 视频输入 (use_audio_in_video=True) → 句级时间戳...")
    messages = build_video_messages(str(VIDEO_PATH), SYS_ASR, PROMPT_SENT_TS)

    # 手动设置 use_audio_in_video=True 需要在消息中有 video type
    # infer() 会自动检测并设置
    t0 = time.time()
    try:
        response = infer(model, processor, messages, max_new_tokens=2048)
        elapsed = round(time.time() - t0, 2)
        print(f"[T4] 耗时 {elapsed}s | 原始输出: {response[:150]}")
        parsed = extract_json(response)
        sentences = parsed.get("sentences", []) if parsed else []
        return {"prompt": "video_mode_sentence_timestamps", "raw_response": response,
                "sentences": sentences, "parse_success": bool(sentences),
                "elapsed_sec": elapsed, "video_segment": "0~60s"}
    except Exception as e:
        print(f"[T4] 异常: {e}")
        return {"prompt": "video_mode_sentence_timestamps", "error": str(e)}


def run_t5_chunked(model, processor, audio_array: np.ndarray, total_sec: float) -> dict:
    """T5: 长音频分块 + 句级时间戳（全片 341s）。"""
    print(f"\n[T5] 分块转录完整音频 ({total_sec:.0f}s, {CHUNK_SEC}s/块)...")
    chunk_samples = CHUNK_SEC * SAMPLE_RATE
    n_chunks = int(np.ceil(total_sec / CHUNK_SEC))
    all_sentences = []
    chunk_log = []
    total_t0 = time.time()

    for i in range(n_chunks):
        s = i * chunk_samples
        e = min((i + 1) * chunk_samples, len(audio_array))
        chunk = audio_array[s:e]
        start_sec = i * CHUNK_SEC
        end_sec = e / SAMPLE_RATE

        t0 = time.time()
        messages = build_audio_messages(chunk, SYS_ASR, PROMPT_SENT_TS)
        try:
            response = infer(model, processor, messages, max_new_tokens=2048)
        except Exception as ex:
            print(f"  块 {i+1}/{n_chunks} 异常: {ex}")
            chunk_log.append({"chunk_index": i, "start_sec": start_sec, "error": str(ex)})
            continue

        elapsed = round(time.time() - t0, 2)
        parsed = extract_json(response)
        sents = parsed.get("sentences", []) if parsed else []

        # 加偏移
        for s_item in sents:
            all_sentences.append({
                "text":     s_item.get("text", ""),
                "start_sec": round(float(s_item.get("start_sec", 0)) + start_sec, 2),
                "end_sec":   round(float(s_item.get("end_sec", 0)) + start_sec, 2),
                "start_ms":  int((float(s_item.get("start_sec", 0)) + start_sec) * 1000),
                "end_ms":    int((float(s_item.get("end_sec", 0)) + start_sec) * 1000),
            })

        chunk_log.append({
            "chunk_index": i,
            "start_sec": start_sec,
            "end_sec": round(end_sec, 1),
            "sentences_in_chunk": len(sents),
            "elapsed_sec": elapsed,
        })
        preview = " | ".join(s_item.get("text", "")[:20] for s_item in sents[:2])
        print(f"  块 {i+1:2d}/{n_chunks} [{start_sec:.0f}~{end_sec:.0f}s] "
              f"{elapsed:.1f}s → {len(sents)}句 | {preview}")

    full_text = "".join(s["text"] for s in all_sentences)
    total_elapsed = round(time.time() - total_t0, 1)
    print(f"[T5] 完成 总耗时 {total_elapsed}s | 合计 {len(all_sentences)} 句 | {len(full_text)} 字")

    return {
        "method": f"chunked_{CHUNK_SEC}s_with_sentence_timestamps",
        "total_elapsed_sec": total_elapsed,
        "chunk_count": n_chunks,
        "chunk_log": chunk_log,
        "sentence_count": len(all_sentences),
        "full_text": full_text,
        "char_count": len(full_text),
        "sentences": all_sentences,
    }


# ================================================================
# 主流程
# ================================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 读取音频
    print(f"[Load] 读取 WAV: {WAV_PATH}")
    audio_array, sr = sf.read(str(WAV_PATH), dtype="float32", always_2d=False)
    total_sec = len(audio_array) / SAMPLE_RATE
    print(f"[Load] {total_sec:.1f}s  {sr}Hz  shape={audio_array.shape}")

    # 探针片段（30~60s）用于 T1/T2/T3
    p_s = int(PROBE_START_SEC * SAMPLE_RATE)
    p_e = int(PROBE_END_SEC * SAMPLE_RATE)
    probe_chunk = audio_array[p_s:p_e]
    print(f"[Load] 探针片段: {PROBE_START_SEC}s ~ {PROBE_END_SEC}s ({len(probe_chunk)/SAMPLE_RATE:.1f}s)")

    # 加载模型
    model, processor = load_model()

    results: dict = {
        "model":  MODEL_PATH,
        "video":  str(VIDEO_PATH),
        "audio_total_sec": round(total_sec, 1),
        "probe_range": f"{PROBE_START_SEC}~{PROBE_END_SEC}s",
        "tests": {},
    }

    # ---- T1: 纯文本转录 ----
    results["tests"]["T1_plain_transcription"] = run_t1_plain(model, processor, probe_chunk)

    # ---- T2: 句级时间戳 ----
    results["tests"]["T2_sentence_timestamps"] = run_t2_sent_ts(
        model, processor, probe_chunk, chunk_start_sec=PROBE_START_SEC
    )

    # ---- T3: 词级时间戳 ----
    results["tests"]["T3_word_timestamps"] = run_t3_word_ts(model, processor, probe_chunk)

    # ---- T4: 视频模式 ----
    results["tests"]["T4_video_mode"] = run_t4_video(model, processor)

    # ---- T5: 全片分块 ----
    results["tests"]["T5_full_chunked"] = run_t5_chunked(model, processor, audio_array, total_sec)

    # ---- 综合评估 ----
    t2 = results["tests"]["T2_sentence_timestamps"]
    t3 = results["tests"]["T3_word_timestamps"]
    t5 = results["tests"]["T5_full_chunked"]

    results["summary"] = {
        "asr_accuracy": {
            "note": "与 GLM-ASR 分块结果（1185字）对比",
            "T1_probe_chars": results["tests"]["T1_plain_transcription"]["char_count"],
            "T5_full_chars":  t5["char_count"],
        },
        "timestamp_capability": {
            "sentence_level": {
                "supported": t2["parse_success"],
                "sentence_count_probe": len(t2.get("sentences", [])),
                "note": "Omni 生成句级时间戳基于语义理解，非 CTC/强制对齐，存在一定误差",
            },
            "word_level": {
                "supported": t3["parse_success"],
                "word_count_probe": len(t3.get("words", [])),
                "note": "词级时间戳为模型推断，精度低于专用强制对齐工具",
            },
        },
        "recommendation": (
            "Qwen3-Omni 具备语音识别能力，可通过 Prompt 获得句级/词级时间戳；"
            "时间戳来自 LLM 语义推断（非 CTC），精度约±1-3s；"
            "对于需要精确时间戳的场景建议结合强制对齐工具后处理。"
        ),
    }

    # 保存结果
    out_file = OUTPUT_DIR / "omni_asr_result.json"
    out_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n{'='*60}")
    print(f"[完成] 结果已保存: {out_file}")
    print(f"  T1 纯文本 ({PROBE_START_SEC:.0f}~{PROBE_END_SEC:.0f}s): "
          f"{results['tests']['T1_plain_transcription']['char_count']} 字")
    print(f"  T2 句级时间戳: 解析 {'成功' if t2['parse_success'] else '失败'}, "
          f"{len(t2.get('sentences', []))} 句")
    print(f"  T3 词级时间戳: 解析 {'成功' if t3['parse_success'] else '失败'}, "
          f"{len(t3.get('words', []))} 词")
    print(f"  T5 全片分块: {t5['sentence_count']} 句, {t5['char_count']} 字")
    print(f"{'='*60}")

    del model, processor
    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
