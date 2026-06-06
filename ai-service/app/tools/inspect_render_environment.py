import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def main() -> None:
    ffmpeg_bin = _resolve_ffmpeg_bin()
    ffprobe_bin = _resolve_ffprobe_bin(ffmpeg_bin)
    filters = _load_ffmpeg_filters(ffmpeg_bin)
    payload = {
        "ffmpeg": {
            "path": ffmpeg_bin,
            "ffprobePath": ffprobe_bin,
            "available": bool(ffmpeg_bin),
            "hasSubtitles": "subtitles" in filters,
            "hasDrawtext": "drawtext" in filters,
            "hasAss": "ass" in filters,
            "hasOverlay": "overlay" in filters,
            "hasXfade": "xfade" in filters,
            "hasAcrossfade": "acrossfade" in filters,
            "hasLoudnorm": "loudnorm" in filters,
        },
        "hyperframes": {
            "availableViaNpx": _command_succeeds(["npx", "--yes", "hyperframes", "--version"]),
        },
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _resolve_ffmpeg_bin() -> Optional[str]:
    candidates = [
        "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
        shutil.which("ffmpeg"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _resolve_ffprobe_bin(ffmpeg_bin: Optional[str]) -> Optional[str]:
    if ffmpeg_bin:
        ffprobe_path = Path(ffmpeg_bin).with_name("ffprobe")
        if ffprobe_path.exists():
            return str(ffprobe_path)
    return shutil.which("ffprobe")


def _load_ffmpeg_filters(ffmpeg_bin: Optional[str]) -> set[str]:
    if not ffmpeg_bin:
        return set()
    process = subprocess.run(
        [ffmpeg_bin, "-hide_banner", "-filters"],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        return set()
    filters = set()
    for line in process.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].endswith((".", "S", "T", "|")):
            filters.add(parts[1])
    return filters


def _command_succeeds(command: list[str]) -> bool:
    if not shutil.which(command[0]):
        return False
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=8)
        return process.returncode == 0
    except subprocess.TimeoutExpired:
        return False


if __name__ == "__main__":
    main()
