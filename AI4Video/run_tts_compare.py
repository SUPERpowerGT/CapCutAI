"""Qwen3-TTS 调研脚本: CustomVoice (预置音色) vs VoiceDesign (自然语言描述音色)。

测试设计:
  - CustomVoice: 选取 2 个差异明显的预置 speaker (Vivian / Uncle_Fu),
    在同一段中文文本上对比合成效果.
  - VoiceDesign: 用 2 段不同的自然语言 instruct 描述,
    在同一段中文文本上对比合成效果.

所有产物 (wav + 元数据 JSON) 会落盘到 outputs/tts_compare/.
"""

from __future__ import annotations

import gc
import json
import time
from pathlib import Path
from typing import Any

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

# ============= 配置区 =============
CUSTOM_VOICE_PATH = "Qwen3-TTS-12Hz-1.7B-CustomVoice"
VOICE_DESIGN_PATH = "Qwen3-TTS-12Hz-1.7B-VoiceDesign"
OUTPUT_DIR = Path("AI4Video/outputs/tts_compare")

# ---- CustomVoice: 同一段文本, 两个差异最大的预置音色 ----
CUSTOM_VOICE_TEXT = (
    "夜深了，我一个人坐在窗前，望着远处的灯火，"
    "心里突然涌起一股说不清的情绪。"
)
CUSTOM_VOICE_CASES = [
    {
        "id": "vivian_chinese",
        "speaker": "Vivian",
        "speaker_desc": "Bright, slightly edgy young female voice (Chinese)",
        "instruct": "",
    },
    {
        "id": "uncle_fu_chinese",
        "speaker": "Uncle_Fu",
        "speaker_desc": "Seasoned male voice with a low, mellow timbre (Chinese)",
        "instruct": "",
    },
]

# ---- VoiceDesign: 同一段文本, 两段差异极大的自然语言描述 ----
VOICE_DESIGN_TEXT = (
    "听说，这次他真的回来了。已经整整十年了，"
    "谁也不曾忘记那个夏天发生的事。"
)
VOICE_DESIGN_CASES = [
    {
        "id": "elderly_male_narrator",
        "instruct": (
            "成熟稳重的中年男性嗓音，音色低沉浑厚，略带沙哑的颗粒感；"
            "语速偏慢，咬字清晰，带着沉思与追忆的气息，像是在讲述一段尘封的往事。"
        ),
    },
    {
        "id": "lively_young_female",
        "instruct": (
            "活泼俏皮的少女声音，音调偏高，语速轻快灵动，"
            "句尾微微上扬，带着兴奋和八卦感，像是在和闺蜜分享一个惊人的消息。"
        ),
    },
]
# =================================


def _save_wav(wav, sr: int, path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, wav, sr)
    return {
        "wav_path": str(path),
        "samples": int(getattr(wav, "shape", (len(wav),))[0]),
        "sample_rate": int(sr),
        "duration_sec": float(len(wav) / sr),
        "bytes": path.stat().st_size,
    }


def _free_model(model) -> None:
    del model
    gc.collect()
    torch.cuda.empty_cache()


def run_custom_voice() -> list[dict[str, Any]]:
    print("\n========== CustomVoice ==========")
    t0 = time.time()
    model = Qwen3TTSModel.from_pretrained(
        CUSTOM_VOICE_PATH,
        device_map="cuda:0",
        dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
    )
    print(f"[CustomVoice] loaded in {time.time() - t0:.1f}s")
    print(f"  supported speakers: {model.get_supported_speakers()}")
    print(f"  supported languages: {model.get_supported_languages()}")

    records: list[dict[str, Any]] = []
    for case in CUSTOM_VOICE_CASES:
        print(f"\n[CustomVoice] -> {case['id']} (speaker={case['speaker']})")
        t_infer = time.time()
        wavs, sr = model.generate_custom_voice(
            text=CUSTOM_VOICE_TEXT,
            language="Chinese",
            speaker=case["speaker"],
            instruct=case["instruct"] or None,
        )
        latency = time.time() - t_infer
        meta = _save_wav(wavs[0], sr, OUTPUT_DIR / f"custom_{case['id']}.wav")
        records.append({
            "model": "Qwen3-TTS-12Hz-1.7B-CustomVoice",
            "text": CUSTOM_VOICE_TEXT,
            "language": "Chinese",
            "latency_sec": latency,
            **case,
            **meta,
        })
        print(f"  latency={latency:.2f}s  duration={meta['duration_sec']:.2f}s  -> {meta['wav_path']}")

    _free_model(model)
    return records


def run_voice_design() -> list[dict[str, Any]]:
    print("\n========== VoiceDesign ==========")
    t0 = time.time()
    model = Qwen3TTSModel.from_pretrained(
        VOICE_DESIGN_PATH,
        device_map="cuda:0",
        dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
    )
    print(f"[VoiceDesign] loaded in {time.time() - t0:.1f}s")

    records: list[dict[str, Any]] = []
    for case in VOICE_DESIGN_CASES:
        print(f"\n[VoiceDesign] -> {case['id']}")
        print(f"  instruct: {case['instruct']}")
        t_infer = time.time()
        wavs, sr = model.generate_voice_design(
            text=VOICE_DESIGN_TEXT,
            language="Chinese",
            instruct=case["instruct"],
        )
        latency = time.time() - t_infer
        meta = _save_wav(wavs[0], sr, OUTPUT_DIR / f"design_{case['id']}.wav")
        records.append({
            "model": "Qwen3-TTS-12Hz-1.7B-VoiceDesign",
            "text": VOICE_DESIGN_TEXT,
            "language": "Chinese",
            "latency_sec": latency,
            **case,
            **meta,
        })
        print(f"  latency={latency:.2f}s  duration={meta['duration_sec']:.2f}s  -> {meta['wav_path']}")

    _free_model(model)
    return records


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_records = {
        "custom_voice": run_custom_voice(),
        "voice_design": run_voice_design(),
    }
    meta_path = OUTPUT_DIR / "metadata.json"
    meta_path.write_text(
        json.dumps(all_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[Saved] metadata -> {meta_path}")


if __name__ == "__main__":
    main()
