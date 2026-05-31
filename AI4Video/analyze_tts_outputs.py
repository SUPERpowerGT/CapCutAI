"""对 outputs/tts_compare/ 下的 4 段 wav 做客观分析:

1. 用 Whisper-large-v3-turbo 反向 ASR, 算字符错误率 (CER) -> 文本保真度.
2. 用 librosa 估计基频 F0 (pyin)、能量 RMS、过零率 ZCR -> 音色客观特征.
3. 汇总到 outputs/tts_compare/analysis.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

WHISPER_PATH = "models/asr/whisper-large-v3-turbo"
TTS_DIR = Path("outputs/tts_compare")


def cer(reference: str, hypothesis: str) -> float:
    """字符错误率: 标准 Levenshtein 距离 / 参考长度."""
    ref = [c for c in reference if not c.isspace()]
    hyp = [c for c in hypothesis if not c.isspace()]
    n, m = len(ref), len(hyp)
    if n == 0:
        return float(len(hyp))
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, m + 1):
            cur = dp[j]
            if ref[i - 1] == hyp[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = cur
    return dp[m] / n


def acoustic_stats(wav: np.ndarray, sr: int) -> dict[str, float]:
    """估计基频均值/标准差、RMS 能量、过零率."""
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    wav = wav.astype(np.float32)

    f0, vflag, _ = librosa.pyin(
        wav,
        fmin=float(librosa.note_to_hz("C2")),   # ~65 Hz
        fmax=float(librosa.note_to_hz("C6")),   # ~1046 Hz
        sr=sr,
    )
    voiced = f0[~np.isnan(f0)] if f0 is not None else np.array([])
    return {
        "f0_mean_hz": float(np.mean(voiced)) if voiced.size else float("nan"),
        "f0_std_hz": float(np.std(voiced)) if voiced.size else float("nan"),
        "voiced_ratio": float(np.mean(vflag)) if vflag is not None and vflag.size else 0.0,
        "rms": float(np.sqrt(np.mean(wav ** 2))),
        "zcr": float(np.mean(librosa.feature.zero_crossing_rate(wav)[0])),
    }


def load_whisper():
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        WHISPER_PATH, dtype=torch.float16, low_cpu_mem_usage=True, use_safetensors=True
    ).to("cuda:0")
    processor = AutoProcessor.from_pretrained(WHISPER_PATH)
    return pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch.float16,
        device="cuda:0",
        chunk_length_s=30,
        batch_size=4,
    )


def main() -> None:
    meta = json.loads((TTS_DIR / "metadata.json").read_text(encoding="utf-8"))
    pipe = load_whisper()

    results: list[dict] = []
    for group, items in meta.items():
        for item in items:
            wav_path = Path(item["wav_path"])
            wav, sr = sf.read(wav_path)
            audio16 = librosa.resample(wav.astype(np.float32), orig_sr=sr, target_sr=16000) if sr != 16000 else wav.astype(np.float32)
            asr = pipe(
                {"raw": audio16, "sampling_rate": 16000},
                generate_kwargs={"task": "transcribe", "language": "chinese"},
            )["text"].strip()
            stats = acoustic_stats(wav, sr)
            err = cer(item["text"], asr)
            print(f"[{group}] {wav_path.name}")
            print(f"  hypothesis: {asr}")
            print(f"  CER       : {err:.3f}")
            print(f"  F0 mean   : {stats['f0_mean_hz']:.1f} Hz")
            print(f"  F0 std    : {stats['f0_std_hz']:.1f} Hz")
            print(f"  voiced %  : {stats['voiced_ratio']*100:.1f}%")
            print(f"  RMS       : {stats['rms']:.3f}")
            print(f"  ZCR       : {stats['zcr']:.3f}")
            results.append({
                "group": group,
                "wav": wav_path.name,
                "id": item.get("id"),
                "speaker": item.get("speaker"),
                "instruct": item.get("instruct"),
                "reference": item["text"],
                "hypothesis": asr,
                "cer": err,
                **stats,
                "duration_sec": item["duration_sec"],
                "sample_rate": sr,
                "tts_latency_sec": item["latency_sec"],
            })

    out = TTS_DIR / "analysis.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[Saved] {out}")


if __name__ == "__main__":
    main()
