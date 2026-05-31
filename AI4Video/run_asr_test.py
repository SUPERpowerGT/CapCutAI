"""ASR 音频转录测试入口。

流程:
  1. 从视频中抽取音轨 -> data/<video>.wav (16kHz mono)。
  2. 用 Qwen3-ASR-1.7B 在不同 language hint 下做转录, 对比效果。
"""

from __future__ import annotations

from pathlib import Path

from framework.asr import Qwen3ASRTester
from framework.audio_utils import extract_audio_from_video
from framework.tasks import ASR_TASKS

# ============= 配置区 (按需修改) =============
VIDEO_PATH = "data/3246165181.mp4"
ASR_MODEL_PATH = "models/asr/Qwen3-ASR-1.7B"
ASR_MODEL_NAME = "Qwen3-ASR-1.7B"

OUTPUT_DIR = Path("outputs")
AUDIO_DIR = Path("data")
# =============================================


def main() -> None:
    video_path = Path(VIDEO_PATH)
    if not video_path.exists():
        raise FileNotFoundError(f"未找到视频: {video_path}")

    audio_path = AUDIO_DIR / f"{video_path.stem}.wav"
    if not audio_path.exists():
        print(f"[Extract] {video_path.name} -> {audio_path.name}")
        extract_audio_from_video(video_path, audio_path)
    print(f"[Audio ready] {audio_path}")

    tester = Qwen3ASRTester(
        model_path=ASR_MODEL_PATH,
        name=ASR_MODEL_NAME,
        attn_implementation="flash_attention_2",
    )
    results = tester.run_tasks(str(audio_path), ASR_TASKS)
    tester.save_results(results, OUTPUT_DIR / f"asr_{ASR_MODEL_NAME}.json")


if __name__ == "__main__":
    main()
