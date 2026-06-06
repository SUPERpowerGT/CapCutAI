"""音频工具: 从视频中抽取音轨, 保存为 WAV (16kHz, 单声道, PCM16)。

无需系统级 ffmpeg 二进制, 仅依赖 PyAV (pip install av)。
"""

from __future__ import annotations

from pathlib import Path

import av
import numpy as np


def extract_audio_from_video(
    video_path: str | Path,
    output_path: str | Path | None = None,
    target_sr: int = 16000,
) -> Path:
    """从视频中抽取音轨并保存为 16kHz 单声道 WAV。

    Args:
        video_path: 输入视频路径。
        output_path: 输出 WAV 路径。 默认在视频同目录下生成 <name>.wav。
        target_sr: 输出采样率, 默认 16000Hz (Qwen3-ASR 期望)。

    Returns:
        生成的 WAV 文件绝对路径。
    """
    video_path = Path(video_path)
    if output_path is None:
        output_path = video_path.with_suffix(".wav")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with av.open(str(video_path)) as in_container:
        audio_streams = [s for s in in_container.streams if s.type == "audio"]
        if not audio_streams:
            raise RuntimeError(f"视频 {video_path} 中未找到音轨")
        in_stream = audio_streams[0]

        resampler = av.AudioResampler(format="s16", layout="mono", rate=target_sr)

        with av.open(str(output_path), mode="w") as out_container:
            out_stream = out_container.add_stream("pcm_s16le", rate=target_sr)
            out_stream.layout = "mono"

            for frame in in_container.decode(in_stream):
                for resampled in resampler.resample(frame):
                    for packet in out_stream.encode(resampled):
                        out_container.mux(packet)

            # flush
            for packet in out_stream.encode(None):
                out_container.mux(packet)

    return output_path.resolve()


def load_wav_as_array(wav_path: str | Path) -> tuple[np.ndarray, int]:
    """读取 WAV 文件为 (np.float32 数组, sample_rate)。"""
    with av.open(str(wav_path)) as container:
        stream = next(s for s in container.streams if s.type == "audio")
        sr = stream.rate
        chunks: list[np.ndarray] = []
        for frame in container.decode(stream):
            chunks.append(frame.to_ndarray().flatten())
    audio = np.concatenate(chunks).astype(np.float32)
    # PCM16 -> [-1, 1]
    if audio.dtype != np.float32 or audio.max() > 1.5:
        audio = audio / 32768.0
    return audio, sr
