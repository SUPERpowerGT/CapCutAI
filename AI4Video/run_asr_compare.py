"""ASR 模型对比脚本: Qwen3-ASR-1.7B vs Whisper-large-v3-turbo。

流程:
  1. 从视频中抽取 16kHz 单声道 WAV (复用 framework/audio_utils).
  2. 分别用两个模型对同一段音频做转录.
  3. 将结果落盘为 JSON, 便于后续生成对比 Markdown 报告.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from framework.asr import Qwen3ASRTester
from framework.audio_utils import extract_audio_from_video
from framework.base import TaskResult
from framework.whisper_asr import WhisperASRTester

# ============= 配置区 =============
VIDEO_PATH = Path(
    "data/"
    "8be949d4b3e2d56e21106753884ace77.mp4"
)
QWEN_ASR_PATH = "Qwen3-ASR-1.7B"
WHISPER_PATH = "whisper-large-v3-turbo"

OUTPUT_DIR = Path("outputs/asr_compare")
AUDIO_DIR = Path("data")
# =================================


def _save(results: list[TaskResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[Saved] {path}")


def main() -> None:
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(VIDEO_PATH)

    audio_path = AUDIO_DIR / f"{VIDEO_PATH.stem}.wav"
    if not audio_path.exists():
        print(f"[Extract] {VIDEO_PATH.name} -> {audio_path.name}")
        extract_audio_from_video(VIDEO_PATH, audio_path)
    print(f"[Audio] {audio_path}")

    # ---------- Qwen3-ASR-1.7B ----------
    qwen_tasks = {
        "auto_detect": "auto",
        "force_chinese": "Chinese",
    }
    qwen_tester = Qwen3ASRTester(
        model_path=QWEN_ASR_PATH,
        name="Qwen3-ASR-1.7B",
        attn_implementation="flash_attention_2",
    )
    # Qwen3-ASR 的 return_time_stamps 需要额外加载 forced_aligner, 这里只取纯文本
    qwen_results = qwen_tester.run_tasks(
        str(audio_path),
        qwen_tasks,
        return_time_stamps=False,
    )
    _save(qwen_results, OUTPUT_DIR / "qwen3_asr.json")

    # 释放显存
    del qwen_tester
    import gc, torch
    gc.collect(); torch.cuda.empty_cache()

    # ---------- Whisper-large-v3-turbo ----------
    whisper_tasks = {
        "auto_detect": "",            # 让 Whisper 自动检测
        "force_chinese": "chinese",   # 强制中文
    }
    whisper_tester = WhisperASRTester(
        model_path=WHISPER_PATH,
        name="whisper-large-v3-turbo",
    )
    whisper_results = whisper_tester.run_tasks(
        str(audio_path),
        whisper_tasks,
        return_time_stamps=True,
    )
    _save(whisper_results, OUTPUT_DIR / "whisper_large_v3_turbo.json")


if __name__ == "__main__":
    main()
