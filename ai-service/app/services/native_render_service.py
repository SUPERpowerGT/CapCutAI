import json
import math
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal, Optional


JsonDict = dict[str, Any]
AudioMode = Literal["mute", "source", "external"]


def render_native_video(
    package_path: Path,
    output_path: Optional[Path] = None,
    max_long_side: int = 640,
    fps: Optional[int] = None,
    max_clips: Optional[int] = None,
    max_duration_ms: Optional[int] = None,
    crf: int = 28,
    preset: str = "veryfast",
    audio_mode: AudioMode = "mute",
    external_audio_path: Optional[Path] = None,
    burn_subtitles: bool = False,
    subtitle_font_size: int = 24,
    subtitle_font_name: str = "Heiti SC",
    ffmpeg_bin: Optional[str] = None,
) -> JsonDict:
    export_package = json.loads(package_path.read_text(encoding="utf-8"))
    timeline_plan = export_package["timelinePlan"]
    editing_job = export_package["editingJob"]
    render_result = export_package.get("renderResult", {})

    resolved_output = output_path or Path(editing_job["outputPath"])
    if not resolved_output.is_absolute():
        resolved_output = Path(__file__).resolve().parents[3] / resolved_output
    resolved_output = resolved_output.expanduser().resolve()
    resolved_output.parent.mkdir(parents=True, exist_ok=True)

    resolved_ffmpeg_bin = _resolve_ffmpeg_bin(ffmpeg_bin)
    resolved_ffprobe_bin = _resolve_ffprobe_bin(resolved_ffmpeg_bin)
    resolved_external_audio_path = _resolve_external_audio_path(external_audio_path)
    render_fps = fps or int(editing_job.get("renderHints", {}).get("fps", 30))
    clips = _select_video_clips(timeline_plan, max_clips=max_clips, max_duration_ms=max_duration_ms)
    if not clips:
        raise RuntimeError("No video clips found in timelinePlan.")

    source_materials = {
        material["sourceMaterialId"]: material for material in export_package.get("sourceMaterials", [])
    }
    source_assets = {
        asset["assetId"]: asset for asset in export_package.get("sourceAssets", [])
    }
    resolved_clips = _resolve_clip_sources(
        clips,
        source_materials,
        source_assets,
        ffprobe_bin=resolved_ffprobe_bin,
    )
    if not resolved_clips:
        raise RuntimeError("No video clips could be resolved to local source files.")

    dimensions = _resolve_output_dimensions(
        resolved_clips[0]["sourcePath"],
        max_long_side,
        ffprobe_bin=resolved_ffprobe_bin,
    )
    subtitle_events = _build_subtitle_events(
        resolved_clips=resolved_clips,
        subtitle_clips=_get_track_clips(timeline_plan, "subtitle"),
    )

    with TemporaryDirectory(prefix="capcutai-native-render-") as temp_dir:
        subtitle_path = None
        if burn_subtitles and subtitle_events:
            _ensure_ffmpeg_filter(resolved_ffmpeg_bin, "subtitles")
            subtitle_path = Path(temp_dir) / "subtitles.ass"
            subtitle_path.write_text(
                _build_ass_subtitles(
                    subtitle_events,
                    width=dimensions["width"],
                    height=dimensions["height"],
                    font_size=subtitle_font_size,
                    font_name=subtitle_font_name,
                ),
                encoding="utf-8",
            )

        command = _build_ffmpeg_command(
            resolved_clips=resolved_clips,
            output_path=resolved_output,
            ffmpeg_bin=resolved_ffmpeg_bin,
            width=dimensions["width"],
            height=dimensions["height"],
            fps=render_fps,
            crf=crf,
            preset=preset,
            audio_mode=audio_mode,
            external_audio_path=resolved_external_audio_path,
            subtitle_path=subtitle_path,
        )

        started_at = datetime.now(timezone.utc)
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        completed_at = datetime.now(timezone.utc)

    result = {
        "renderId": render_result.get("renderId", f"render_{timeline_plan['timelineId']}_native"),
        "jobId": editing_job["jobId"],
        "status": "completed" if process.returncode == 0 else "failed",
        "renderer": "ffmpeg-native",
        "outputPath": str(resolved_output),
        "timelineId": timeline_plan["timelineId"],
        "clipCount": len(resolved_clips),
        "width": dimensions["width"],
        "height": dimensions["height"],
        "fps": render_fps,
        "audioMode": audio_mode,
        "externalAudioPath": str(resolved_external_audio_path) if resolved_external_audio_path else None,
        "burnSubtitles": burn_subtitles,
        "subtitleCount": len(subtitle_events) if burn_subtitles else 0,
        "subtitleFontName": subtitle_font_name if burn_subtitles else None,
        "startedAt": started_at.isoformat(),
        "completedAt": completed_at.isoformat(),
        "durationSeconds": (completed_at - started_at).total_seconds(),
        "command": command,
        "ffmpegBin": resolved_ffmpeg_bin,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }
    if process.returncode != 0:
        result["errorMessage"] = process.stderr.strip() or process.stdout.strip()

    result_path = resolved_output.with_suffix(".render-result.json")
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    if process.returncode != 0:
        raise RuntimeError(f"Native ffmpeg render failed: {result['errorMessage']}")

    return {**result, "renderResultPath": str(result_path)}


def _select_video_clips(
    timeline_plan: JsonDict,
    max_clips: Optional[int],
    max_duration_ms: Optional[int],
) -> list[JsonDict]:
    video_clips = []
    for track in timeline_plan.get("tracks", []):
        if track.get("type") == "video":
            video_clips = sorted(track.get("clips", []), key=lambda clip: clip.get("startMs", 0))
            break

    selected = []
    consumed_ms = 0
    for clip in video_clips:
        if max_clips is not None and len(selected) >= max_clips:
            break

        duration_ms = max(1, int(clip.get("durationMs", 0)))
        if max_duration_ms is not None:
            remaining_ms = max_duration_ms - consumed_ms
            if remaining_ms <= 0:
                break
            duration_ms = min(duration_ms, remaining_ms)

        selected.append({**clip, "durationMs": duration_ms})
        consumed_ms += duration_ms

    return selected


def _resolve_clip_sources(
    clips: list[JsonDict],
    source_materials: dict[str, JsonDict],
    source_assets: dict[str, JsonDict],
    ffprobe_bin: str,
) -> list[JsonDict]:
    resolved = []
    output_start_seconds = 0.0
    for clip in clips:
        source_material = source_materials.get(clip.get("sourceMaterialId", ""))
        source_asset = source_assets.get(clip.get("assetId", ""))
        source_path = _resolve_source_video_path(source_material, source_asset)
        if not source_path:
            continue

        duration_seconds = max(0.001, int(clip.get("durationMs", 0)) / 1000)
        resolved.append(
            {
                "sourcePath": source_path,
                "sourceMaterialId": clip.get("sourceMaterialId", ""),
                "timelineStartMs": int(clip.get("startMs", 0)),
                "sourceStartSeconds": max(0, int(clip.get("sourceStartMs", 0))) / 1000,
                "durationSeconds": duration_seconds,
                "outputStartSeconds": output_start_seconds,
                "hasAudio": _probe_has_audio(source_path, ffprobe_bin=ffprobe_bin),
                "label": clip.get("label", ""),
            }
        )
        output_start_seconds += duration_seconds

    return resolved


def _build_ffmpeg_command(
    resolved_clips: list[JsonDict],
    output_path: Path,
    ffmpeg_bin: str,
    width: int,
    height: int,
    fps: int,
    crf: int,
    preset: str,
    audio_mode: AudioMode,
    external_audio_path: Optional[Path],
    subtitle_path: Optional[Path],
) -> list[str]:
    command = [ffmpeg_bin, "-y", "-hide_banner"]
    for clip in resolved_clips:
        command.extend(
            [
                "-ss",
                f"{clip['sourceStartSeconds']:.3f}",
                "-t",
                f"{clip['durationSeconds']:.3f}",
                "-i",
                clip["sourcePath"],
            ]
        )
    if audio_mode == "external":
        if external_audio_path is None:
            raise RuntimeError("audio_mode='external' requires external_audio_path.")
        command.extend(["-i", str(external_audio_path)])

    filters = []
    for index in range(len(resolved_clips)):
        label = f"v{index}"
        filters.append(
            f"[{index}:v]"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,fps={fps},format=yuv420p[{label}]"
        )

    total_duration_seconds = sum(clip["durationSeconds"] for clip in resolved_clips)

    if audio_mode == "source":
        audio_inputs = []
        for index, clip in enumerate(resolved_clips):
            audio_label = f"a{index}"
            if clip["hasAudio"]:
                filters.append(
                    f"[{index}:a]aresample=48000,"
                    f"aformat=sample_fmts=fltp:channel_layouts=stereo,"
                    f"asetpts=PTS-STARTPTS[{audio_label}]"
                )
            else:
                filters.append(
                    f"anullsrc=channel_layout=stereo:sample_rate=48000,"
                    f"atrim=duration={clip['durationSeconds']:.3f},"
                    f"asetpts=PTS-STARTPTS[{audio_label}]"
                )
            audio_inputs.append(f"[{audio_label}]")

        concat_pairs = "".join(
            f"[v{index}][a{index}]" for index in range(len(resolved_clips))
        )
        if subtitle_path:
            filters.append(f"{concat_pairs}concat=n={len(resolved_clips)}:v=1:a=1[basev][outa]")
            filters.append(f"[basev]subtitles=filename='{_escape_filter_path(subtitle_path)}'[outv]")
        else:
            filters.append(f"{concat_pairs}concat=n={len(resolved_clips)}:v=1:a=1[outv][outa]")
    elif audio_mode == "external":
        video_inputs = "".join(f"[v{index}]" for index in range(len(resolved_clips)))
        external_audio_index = len(resolved_clips)
        if subtitle_path:
            filters.append(f"{video_inputs}concat=n={len(resolved_clips)}:v=1:a=0[basev]")
            filters.append(f"[basev]subtitles=filename='{_escape_filter_path(subtitle_path)}'[outv]")
        else:
            filters.append(f"{video_inputs}concat=n={len(resolved_clips)}:v=1:a=0[outv]")
        filters.append(
            f"[{external_audio_index}:a]aresample=48000,"
            f"aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"atrim=duration={total_duration_seconds:.3f},"
            f"asetpts=PTS-STARTPTS[outa]"
        )
    else:
        video_inputs = "".join(f"[v{index}]" for index in range(len(resolved_clips)))
        if subtitle_path:
            filters.append(f"{video_inputs}concat=n={len(resolved_clips)}:v=1:a=0[basev]")
            filters.append(f"[basev]subtitles=filename='{_escape_filter_path(subtitle_path)}'[outv]")
        else:
            filters.append(f"{video_inputs}concat=n={len(resolved_clips)}:v=1:a=0[outv]")

    output_args = [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[outv]",
    ]
    if audio_mode in {"source", "external"}:
        output_args.extend(["-map", "[outa]", "-c:a", "aac", "-b:a", "160k"])
    else:
        output_args.append("-an")

    command.extend(
        output_args
        + [
            "-dn",
            "-map_metadata",
            "-1",
            "-map_chapters",
            "-1",
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-crf",
            str(crf),
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    return command


def _get_track_clips(timeline_plan: JsonDict, track_type: str) -> list[JsonDict]:
    for track in timeline_plan.get("tracks", []):
        if track.get("type") == track_type:
            return sorted(track.get("clips", []), key=lambda clip: clip.get("startMs", 0))
    return []


def _build_subtitle_events(
    resolved_clips: list[JsonDict],
    subtitle_clips: list[JsonDict],
) -> list[JsonDict]:
    events = []
    for video_clip in resolved_clips:
        video_start_ms = video_clip["timelineStartMs"]
        video_end_ms = video_start_ms + int(video_clip["durationSeconds"] * 1000)
        output_start_ms = int(video_clip["outputStartSeconds"] * 1000)

        for subtitle_clip in subtitle_clips:
            subtitle_start_ms = int(subtitle_clip.get("startMs", 0))
            subtitle_end_ms = subtitle_start_ms + int(subtitle_clip.get("durationMs", 0))
            if subtitle_start_ms >= video_end_ms or subtitle_end_ms <= video_start_ms:
                continue

            event_start_ms = output_start_ms + max(subtitle_start_ms, video_start_ms) - video_start_ms
            event_end_ms = output_start_ms + min(subtitle_end_ms, video_end_ms) - video_start_ms
            if event_end_ms <= event_start_ms:
                continue

            events.append(
                {
                    "startMs": event_start_ms,
                    "endMs": event_end_ms,
                    "text": subtitle_clip.get("label", ""),
                }
            )

    return events


def _build_ass_subtitles(
    events: list[JsonDict],
    width: int,
    height: int,
    font_size: int,
    font_name: str,
) -> str:
    margin_v = max(24, int(height * 0.08))
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{font_name},"
        f"{font_size},&H00FFFFFF,&H00FFFFFF,&H8A000000,&H90000000,"
        f"-1,0,0,0,100,100,0,0,1,2,1,2,36,36,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for event in events:
        text = _escape_ass_text(str(event.get("text", "")))
        if not text:
            continue
        lines.append(
            "Dialogue: 0,"
            f"{_format_ass_time(event['startMs'])},"
            f"{_format_ass_time(event['endMs'])},"
            f"Default,,0,0,0,,{text}"
        )
    return "\n".join(lines) + "\n"


def _format_ass_time(value_ms: int) -> str:
    centiseconds = max(0, int(round(value_ms / 10)))
    hours = centiseconds // 360000
    centiseconds %= 360000
    minutes = centiseconds // 6000
    centiseconds %= 6000
    seconds = centiseconds // 100
    centiseconds %= 100
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def _escape_ass_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def _escape_filter_path(path: Path) -> str:
    value = str(path)
    return value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _ensure_ffmpeg_filter(ffmpeg_bin: str, filter_name: str) -> None:
    process = subprocess.run(
        [ffmpeg_bin, "-hide_banner", "-filters"],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0 or filter_name not in process.stdout:
        raise RuntimeError(
            f"Current ffmpeg does not include the '{filter_name}' filter: {ffmpeg_bin}. "
            "Install an ffmpeg build with libass/freetype/fontconfig support, "
            "for example Homebrew ffmpeg-full, then rerun this command."
        )


def _resolve_output_dimensions(video_path: str, max_long_side: int, ffprobe_bin: str) -> JsonDict:
    probed = _probe_video_dimensions(video_path, ffprobe_bin=ffprobe_bin)
    if not probed:
        return {"width": max_long_side, "height": _even(max_long_side * 9 / 16)}

    return _fit_render_dimensions(probed["width"], probed["height"], max_long_side=max_long_side)


def _find_source_video_path(source_case_id: Optional[str]) -> Optional[str]:
    if not source_case_id:
        return None

    case_dir = Path(__file__).resolve().parents[3] / "data" / "test_case" / source_case_id
    if not case_dir.exists():
        return None

    candidates = sorted(
        file_path
        for file_path in case_dir.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in {".mp4", ".mov", ".webm", ".m4v"}
    )
    if not candidates:
        return None

    return str(candidates[0])


def _resolve_source_video_path(
    source_material: Optional[JsonDict],
    source_asset: Optional[JsonDict],
) -> Optional[str]:
    if source_asset:
        object_url = source_asset.get("objectUrl")
        if isinstance(object_url, str) and object_url:
            asset_path = Path(object_url).expanduser()
            if asset_path.exists():
                return str(asset_path.resolve())

    source_case_id = source_material.get("sourceCaseId") if source_material else None
    return _find_source_video_path(source_case_id)


def _probe_video_dimensions(video_path: str, ffprobe_bin: str = "ffprobe") -> Optional[JsonDict]:
    command = [
        ffprobe_bin,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        video_path,
    ]
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        return None

    try:
        payload = json.loads(process.stdout)
        stream = (payload.get("streams") or [])[0]
        return {"width": int(stream["width"]), "height": int(stream["height"])}
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def _probe_has_audio(video_path: str, ffprobe_bin: str = "ffprobe") -> bool:
    command = [
        ffprobe_bin,
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=index",
        "-of",
        "json",
        video_path,
    ]
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        return False

    try:
        payload = json.loads(process.stdout)
        return bool(payload.get("streams"))
    except ValueError:
        return False


def _resolve_ffmpeg_bin(ffmpeg_bin: Optional[str]) -> str:
    if ffmpeg_bin:
        return str(Path(ffmpeg_bin).expanduser())
    env_bin = os.environ.get("CAPCUTAI_FFMPEG_BIN") or os.environ.get("FFMPEG_BIN")
    if env_bin:
        return str(Path(env_bin).expanduser())
    macos_full_bin = Path("/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg")
    if macos_full_bin.exists():
        return str(macos_full_bin)
    return "ffmpeg"


def _resolve_ffprobe_bin(ffmpeg_bin: str) -> str:
    ffmpeg_path = Path(ffmpeg_bin)
    if ffmpeg_path.name == "ffmpeg":
        ffprobe_path = ffmpeg_path.with_name("ffprobe")
        if ffprobe_path.exists():
            return str(ffprobe_path)
    return "ffprobe"


def _resolve_external_audio_path(external_audio_path: Optional[Path]) -> Optional[Path]:
    if external_audio_path is None:
        return None
    resolved = external_audio_path.expanduser().resolve()
    if not resolved.exists():
        raise RuntimeError(f"External audio file does not exist: {resolved}")
    return resolved


def _fit_render_dimensions(width: int, height: int, max_long_side: int) -> JsonDict:
    width = max(1, int(width))
    height = max(1, int(height))
    long_side = max(width, height)
    if long_side <= max_long_side:
        return {"width": _even(width), "height": _even(height)}

    scale = max_long_side / long_side
    return {"width": _even(width * scale), "height": _even(height * scale)}


def _even(value: float) -> int:
    return max(2, int(math.floor(value / 2) * 2))
