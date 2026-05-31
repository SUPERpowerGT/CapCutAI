"""Qwen3-Omni 视频模式 ASR 实验验证脚本。

实验目标
--------
验证能否在 orchestrator 阶段用「单次 Omni 推理 + 视频输入」同时完成音频识别和
视频理解，从而把 ASR 步骤与认知对齐步骤合并为一次模型调用。

测试方案
--------
  T1  60s 音频片段（numpy array）→ 纯 ASR 句级时间戳          （基准，复现上次分块结果）
  T2  60s 视频片段（use_audio_in_video=True）→ 纯 ASR 句级时间戳 （验证视频模式 ASR 准确度）
  T3  全片 341s 视频 → 「单次联合推理」：口播转录 + 叙事结构 JSON  （验证合并方案可行性）

对比基准
--------
  分块音频 T5 结果：58句，1193字（run_omni_asr_test.py 已验证）

用法
----
  python run_omni_video_asr_test.py
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
MODEL_PATH = "Qwen3-Omni-30B-A3B-Instruct"
VIDEO_PATH = Path("data/283851334-1-208.mp4")
WAV_PATH   = Path("AI4Video/outputs/glm_asr_test/test_audio.wav")
OUTPUT_DIR = Path("AI4Video/outputs/omni_video_asr_test")

SAMPLE_RATE = 16000
PROBE_START = 30.0   # 60s 测试片段起点（T1/T2 共用）
PROBE_END   = 90.0   # 60s 测试片段终点

# ================================================================
# 提示词
# ================================================================

SYS_ASR = "你是专业的语音识别助手，能准确转录中文口播内容，并输出句级时间戳。"

PROMPT_ASR = """请对音频（或视频中的音频轨）进行语音识别，输出句级时间戳。

严格按以下 JSON 格式输出，不要添加任何额外文字：
{"sentences": [{"text": "句子内容", "start_sec": 0.0, "end_sec": 2.5}]}

要求：
1. 按自然语句断句（句号/问号/感叹号或语义完整短句）
2. start_sec/end_sec 是相对于本段音频/视频起始的秒数（精度 0.1s）
3. 若无人声则返回 {"sentences": []}
4. 不识别背景音乐，只识别人声口播"""

# 联合推理提示（T3：同时输出 ASR + 叙事结构）
PROMPT_COMBINED = """你是专业 AI 视频剪辑师和语音识别专家。
请对视频完成两项任务，输出合并的 JSON：

任务A：语音识别（人声口播转录，含句级时间戳）
任务B：叙事结构分析（识别视频叙事阶段）

严格按以下 JSON 格式输出，不要添加任何额外文字：
{
  "transcript": {
    "sentences": [{"text": "句子内容", "start_sec": 0.0, "end_sec": 2.5}]
  },
  "storyline_phases": [
    {
      "phase_id": "PHASE_HOOK",
      "energy_level": "HIGH",
      "start_sec": 0.0,
      "end_sec": 60.0,
      "narrative_goal": "该阶段叙事目标（中文，30字以内）"
    }
  ],
  "driving_mode": "TEXT_LOGIC_DRIVEN 或 AUDIO_VISUAL_EMOTION",
  "pacing_style": "HIGH_CONTRAST_FAST 或 STEADY_NARRATIVE 或 EMOTIONAL_SLOW"
}

要求：
- transcript.sentences 的时间戳相对于视频起始（秒）
- storyline_phases 按时间顺序，覆盖整个视频，2~4个阶段
- 仅识别人声口播，不识别背景音乐"""


# ================================================================
# 工具函数
# ================================================================

def load_model():
    print(f"[Model] 加载 Qwen3-Omni: {MODEL_PATH}")
    t0 = time.time()
    model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
        MODEL_PATH,
        dtype="auto",
        device_map="auto",
        attn_implementation="flash_attention_2",
    )
    processor = Qwen3OmniMoeProcessor.from_pretrained(MODEL_PATH)
    print(f"[Model] 加载完成 {time.time()-t0:.1f}s")
    return model, processor


def infer_audio(model, processor, audio_array: np.ndarray, prompt: str,
                max_new_tokens: int = 2048) -> tuple[str, float]:
    """音频数组 → 推理。"""
    messages = [
        {"role": "system", "content": [{"type": "text", "text": SYS_ASR}]},
        {"role": "user", "content": [
            {"type": "audio", "audio": audio_array},
            {"type": "text", "text": prompt},
        ]},
    ]
    return _run_infer(model, processor, messages, use_audio_in_video=False,
                      max_new_tokens=max_new_tokens)


def infer_video(model, processor, video_path: str, prompt: str,
                fps: float = 0.5, max_new_tokens: int = 2048) -> tuple[str, float]:
    """视频文件路径 → 推理（use_audio_in_video=True）。"""
    messages = [
        {"role": "system", "content": [{"type": "text", "text": SYS_ASR}]},
        {"role": "user", "content": [
            {"type": "video", "video": video_path, "fps": fps},
            {"type": "text", "text": prompt},
        ]},
    ]
    return _run_infer(model, processor, messages, use_audio_in_video=True,
                      max_new_tokens=max_new_tokens)


def _run_infer(model, processor, messages, use_audio_in_video: bool,
               max_new_tokens: int) -> tuple[str, float]:
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

    t0 = time.time()
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            thinker_return_dict_in_generate=True,
            use_audio_in_video=use_audio_in_video,
            return_audio=False,
        )
    elapsed = round(time.time() - t0, 2)

    text_ids = outputs[0] if isinstance(outputs, tuple) else outputs
    sequences = text_ids.sequences if hasattr(text_ids, "sequences") else text_ids
    in_len = inputs["input_ids"].shape[1]
    response = processor.batch_decode(sequences[:, in_len:], skip_special_tokens=True)[0]
    return response, elapsed


def extract_json(text: str) -> dict | None:
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def parse_sentences(data: dict | None, offset_sec: float = 0.0) -> list[dict]:
    if not data:
        return []
    sents = data.get("sentences", [])
    return [
        {
            "text": s.get("text", ""),
            "start_sec": round(float(s.get("start_sec", 0)) + offset_sec, 2),
            "end_sec":   round(float(s.get("end_sec", 0)) + offset_sec, 2),
        }
        for s in sents if s.get("text")
    ]


def char_count(sentences: list[dict]) -> int:
    return sum(len(s["text"]) for s in sentences)


# ================================================================
# 测试用例
# ================================================================

def run_t1_audio_baseline(model, processor, audio_array: np.ndarray) -> dict:
    """T1: 60s 音频片段 → 纯 ASR（基准，验证与上次 T2 的一致性）。"""
    print("\n" + "="*60)
    print("[T1] 音频模式 60s ASR（基准）")
    probe = audio_array[int(PROBE_START * SAMPLE_RATE): int(PROBE_END * SAMPLE_RATE)]
    response, elapsed = infer_audio(model, processor, probe, PROMPT_ASR)
    data = extract_json(response)
    sentences = parse_sentences(data, offset_sec=PROBE_START)
    print(f"[T1] 耗时={elapsed}s | {len(sentences)}句 | {char_count(sentences)}字")
    if sentences:
        for s in sentences[:3]:
            print(f"     [{s['start_sec']}~{s['end_sec']}s] {s['text'][:40]}")
    else:
        print(f"[T1] JSON 解析失败，原始: {response[:200]}")
    return {
        "mode": "audio_60s",
        "elapsed_sec": elapsed,
        "sentence_count": len(sentences),
        "char_count": char_count(sentences),
        "sentences": sentences,
        "raw_response": response,
    }


def run_t2_video_asr(model, processor) -> dict:
    """T2: 60s 视频片段（use_audio_in_video=True）→ 纯 ASR。

    注意：不使用 video_start/video_end 参数（已知可能引发问题）。
    传入完整视频但只请求 60s 内容的 ASR — 通过 fps=0.5 控制帧采样量。
    """
    print("\n" + "="*60)
    print("[T2] 视频模式（use_audio_in_video=True）60s ASR")
    print(f"     fps=0.5，完整视频但只问 {PROBE_START}~{PROBE_END}s 的口播内容")

    # 在 prompt 中明确指定需要识别的时间范围
    prompt_scoped = f"""请对视频中 {PROBE_START:.0f}~{PROBE_END:.0f} 秒内的人声口播进行语音识别。

严格按以下 JSON 格式输出：
{{"sentences": [{{"text": "句子内容", "start_sec": {PROBE_START:.0f}.0, "end_sec": {PROBE_END:.0f}.0}}]}}

start_sec/end_sec 是相对于视频起始的绝对秒数。若该段无人声则返回 {{"sentences": []}}"""

    try:
        response, elapsed = infer_video(
            model, processor, str(VIDEO_PATH), prompt_scoped,
            fps=0.5, max_new_tokens=2048
        )
        data = extract_json(response)
        sentences = parse_sentences(data)
        print(f"[T2] 耗时={elapsed}s | {len(sentences)}句 | {char_count(sentences)}字")
        if sentences:
            for s in sentences[:3]:
                print(f"     [{s['start_sec']}~{s['end_sec']}s] {s['text'][:40]}")
        else:
            print(f"[T2] JSON 解析失败，原始: {response[:300]}")
        return {
            "mode": "video_60s_scoped",
            "elapsed_sec": elapsed,
            "sentence_count": len(sentences),
            "char_count": char_count(sentences),
            "sentences": sentences,
            "raw_response": response,
        }
    except Exception as e:
        print(f"[T2] 异常: {type(e).__name__}: {e}")
        return {"mode": "video_60s_scoped", "error": str(e)}


def run_t3_video_combined(model, processor) -> dict:
    """T3: 全片视频 → 联合推理（ASR + 叙事结构），验证「单次调用」方案可行性。

    这是最理想的方案：一次 Omni 调用同时输出口播转录和叙事阶段划分。
    如果成功，可完全省去单独的 ASR 步骤。
    """
    print("\n" + "="*60)
    print("[T3] 全片视频（341s）联合推理：ASR + 叙事结构（fps=0.3）")
    try:
        response, elapsed = infer_video(
            model, processor, str(VIDEO_PATH), PROMPT_COMBINED,
            fps=0.3, max_new_tokens=4096
        )
        data = extract_json(response)
        if data:
            transcript_data = data.get("transcript", {})
            sentences = parse_sentences(transcript_data)
            phases = data.get("storyline_phases", [])
            driving_mode = data.get("driving_mode", "")
            print(f"[T3] 耗时={elapsed}s")
            print(f"     ASR: {len(sentences)}句 | {char_count(sentences)}字")
            print(f"     叙事阶段: {len(phases)} 个")
            print(f"     驱动模式: {driving_mode}")
            if sentences:
                print("     前3句:")
                for s in sentences[:3]:
                    print(f"       [{s['start_sec']}~{s['end_sec']}s] {s['text'][:40]}")
            if phases:
                print("     叙事阶段:")
                for p in phases:
                    print(f"       {p.get('phase_id')} [{p.get('start_sec')}~{p.get('end_sec')}s] {p.get('narrative_goal','')[:30]}")
        else:
            sentences, phases = [], []
            print(f"[T3] JSON 解析失败，原始输出（前500字）:\n{response[:500]}")
        return {
            "mode": "video_full_combined",
            "elapsed_sec": elapsed,
            "asr_sentence_count": len(sentences),
            "asr_char_count": char_count(sentences),
            "asr_sentences": sentences,
            "storyline_phases": phases,
            "driving_mode": data.get("driving_mode", "") if data else "",
            "pacing_style": data.get("pacing_style", "") if data else "",
            "raw_response": response,
            "parse_success": bool(data and sentences),
        }
    except Exception as e:
        print(f"[T3] 异常: {type(e).__name__}: {e}")
        return {"mode": "video_full_combined", "error": str(e)}


# ================================================================
# 主流程
# ================================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[Load] WAV: {WAV_PATH}")
    audio_array, sr = sf.read(str(WAV_PATH), dtype="float32", always_2d=False)
    total_sec = len(audio_array) / SAMPLE_RATE
    print(f"[Load] 总时长={total_sec:.1f}s  shape={audio_array.shape}")

    model, processor = load_model()

    results: dict = {
        "model": MODEL_PATH,
        "video": str(VIDEO_PATH),
        "probe_range_sec": f"{PROBE_START}~{PROBE_END}",
        "baseline_ref": "run_omni_asr_test.py T5: 58句，1193字（分块音频ASR）",
        "tests": {},
    }

    # T1: 音频基准
    results["tests"]["T1_audio_baseline"] = run_t1_audio_baseline(model, processor, audio_array)

    # T2: 视频模式 ASR
    results["tests"]["T2_video_asr"] = run_t2_video_asr(model, processor)

    # T3: 全片联合推理
    results["tests"]["T3_video_combined"] = run_t3_video_combined(model, processor)

    # ---- 可行性评估 ----
    t1 = results["tests"]["T1_audio_baseline"]
    t2 = results["tests"]["T2_video_asr"]
    t3 = results["tests"]["T3_video_combined"]

    t2_ok = t2.get("sentence_count", 0) > 0 and "error" not in t2
    t3_ok = t3.get("asr_sentence_count", 0) > 0 and t3.get("parse_success", False)

    results["feasibility"] = {
        "T1_audio_asr_works": t1.get("sentence_count", 0) > 0,
        "T2_video_asr_works": t2_ok,
        "T3_combined_works": t3_ok,
        "recommendation": (
            "✓ 推荐单次联合推理（T3方案）：一次调用同时完成 ASR + 叙事结构，节省模型加载开销"
            if t3_ok else
            "✓ 推荐分块音频 ASR（T1基准方案）+ 时间戳对齐后喂给 orchestrator"
            if t1.get("sentence_count", 0) > 0 else
            "✗ 需进一步排查 ASR 输出问题"
        ),
        "T2_video_vs_T1_audio": (
            f"T2({t2.get('char_count',0)}字) vs T1({t1.get('char_count',0)}字)"
            if not t2.get("error") else f"T2 失败: {t2.get('error','')}"
        ),
        "T3_asr_chars": t3.get("asr_char_count", 0),
        "T3_phases_count": len(t3.get("storyline_phases", [])),
    }

    out_file = OUTPUT_DIR / "omni_video_asr_result.json"
    out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"[完成] 结果已保存: {out_file}")
    print(f"  T1(音频基准): {t1.get('sentence_count',0)}句 {t1.get('char_count',0)}字")
    print(f"  T2(视频ASR):  {'失败:'+t2.get('error','')[:40] if t2.get('error') else str(t2.get('sentence_count',0))+'句 '+str(t2.get('char_count',0))+'字'}")
    print(f"  T3(联合推理): ASR={t3.get('asr_sentence_count',0)}句 阶段={len(t3.get('storyline_phases',[]))}个")
    print(f"  推荐方案: {results['feasibility']['recommendation'][:60]}")
    print(f"{'='*60}")

    del model, processor
    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
