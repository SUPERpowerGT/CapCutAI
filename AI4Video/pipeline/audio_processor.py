"""步骤1: 音频特征提取 —— BPM、节拍时间点（Beats）、高潮能量点（Drops）。

依赖: librosa, numpy（函数内懒加载，避免无 GPU/av 环境下导入失败）
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AudioFeatures:
    bpm: float
    beats_ms: list[int]    # 每个节拍的绝对时间（毫秒）
    drops_ms: list[int]    # 高潮能量爆发点的绝对时间（毫秒）
    duration_ms: int


def extract_audio_features(
    video_path: str | Path,
    wav_cache_path: str | Path | None = None,
    drops_top_n: int = 3,
) -> AudioFeatures:
    """从视频中提取音频特征。

    wav_cache_path 若指定且文件已存在则复用，否则从视频中重新提取。
    """
    import librosa
    import numpy as np
    from framework.audio_utils import extract_audio_from_video, load_wav_as_array

    video_path = Path(video_path)

    if wav_cache_path and Path(wav_cache_path).exists():
        wav_path = Path(wav_cache_path)
    else:
        wav_path = extract_audio_from_video(video_path, wav_cache_path)

    audio, sr = load_wav_as_array(wav_path)
    duration_ms = int(len(audio) / sr * 1000)

    tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr, units="frames")
    bpm = float(np.atleast_1d(tempo)[0])
    beats_ms = [int(librosa.frames_to_time(f, sr=sr) * 1000) for f in beat_frames]

    drops_ms = _detect_drops(audio, sr, top_n=drops_top_n)

    return AudioFeatures(bpm=bpm, beats_ms=beats_ms, drops_ms=drops_ms, duration_ms=duration_ms)


def _detect_drops(audio, sr: int, top_n: int = 3) -> list[int]:
    """检测音频中的高潮能量爆发点（Drops）。

    策略: 将起始强度（onset strength）做平滑后寻找局部极大值，
    取强度最高的 top_n 个且彼此间距不小于 2 秒的峰值。
    """
    import librosa
    import numpy as np

    hop_length = 512
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop_length)
    times = librosa.times_like(onset_env, sr=sr, hop_length=hop_length)

    window = max(1, int(sr / hop_length * 0.5))
    kernel = np.ones(window) / window
    smoothed = np.convolve(onset_env, kernel, mode="same")
    threshold = smoothed.mean() + smoothed.std() * 1.5

    candidates: list[tuple[float, int]] = []
    for i in range(1, len(smoothed) - 1):
        if smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1] and smoothed[i] > threshold:
            candidates.append((smoothed[i], i))

    candidates.sort(reverse=True)
    selected_ms: list[int] = []
    for _, idx in candidates:
        t_ms = int(times[idx] * 1000)
        if all(abs(t_ms - s) >= 2000 for s in selected_ms):
            selected_ms.append(t_ms)
        if len(selected_ms) >= top_n:
            break

    return sorted(selected_ms)
