"""在给定秒数从视频截取一帧并保存为 JPEG。

纯 PyAV 实现, 无 ffmpeg 二进制依赖。
策略: seek 到目标时间戳, 然后向前解码直到拿到一帧覆盖该时间点。
"""

from __future__ import annotations

from pathlib import Path

import av


class VideoFrameExtractor:
    """对单个视频文件持有解码器, 可多次随机取帧。"""

    def __init__(self, video_path: str | Path):
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(self.video_path)
        self._container = av.open(str(self.video_path))
        self._stream = next(s for s in self._container.streams if s.type == "video")
        self._stream.thread_type = "AUTO"

        # 视频总时长 (秒); 容器层 duration 已是秒 (av container.duration 单位是微秒 * AV_TIME_BASE)
        if self._container.duration is not None:
            self.duration_sec = float(self._container.duration) / av.time_base
        else:
            self.duration_sec = float(self._stream.duration * self._stream.time_base)

    def close(self) -> None:
        self._container.close()

    def __enter__(self) -> "VideoFrameExtractor":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def extract_frame(self, target_sec: float, output_path: str | Path) -> Path:
        """截取最接近 target_sec 的一帧, 保存为 JPEG。"""
        target_sec = max(0.0, min(target_sec, self.duration_sec - 1e-3))
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # PyAV seek: 单位为 stream time_base; av.time_base = 1_000_000
        seek_offset = int(target_sec / self._stream.time_base)
        self._container.seek(seek_offset, any_frame=False, backward=True, stream=self._stream)

        chosen = None
        for frame in self._container.decode(self._stream):
            t = float(frame.pts * frame.time_base) if frame.pts is not None else 0.0
            chosen = frame
            if t >= target_sec:
                break

        if chosen is None:
            raise RuntimeError(f"无法在 {target_sec:.2f}s 截取帧: {self.video_path}")

        img = chosen.to_image()  # PIL.Image (RGB)
        img.save(output_path, format="JPEG", quality=88)
        return output_path.resolve()


def extract_frames_for_timestamps(
    video_path: str | Path,
    seconds: list[float],
    output_dir: str | Path,
    name_prefix: str = "frame",
) -> list[Path]:
    """批量在一个视频里多次截帧, 返回保存路径列表。"""
    output_dir = Path(output_dir)
    paths: list[Path] = []
    with VideoFrameExtractor(video_path) as ext:
        for i, t in enumerate(seconds):
            out = output_dir / f"{name_prefix}_{i:02d}_{t:06.2f}s.jpg"
            paths.append(ext.extract_frame(t, out))
    return paths
