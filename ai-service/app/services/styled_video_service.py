from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.editing_planner_service import create_timeline_plan_with_llm


@dataclass(frozen=True)
class StyledVideoRun:
    workspace_id: str
    reference_video: Path | None
    source_videos: list[Path]
    reference_output_dir: Path
    source_output_dirs: list[Path]
    timeline_plan_path: Path
    planner_info_path: Path
    package_path: Path
    render_output_path: Path
    render_result_path: Path
    external_audio_path: Path | None


def create_styled_video_from_workspace(
    workspace: dict[str, Any],
    assets: dict[str, Any],
    *,
    conversation_id: str,
    user_instruction: str = "",
) -> dict[str, Any]:
    reference_video = _resolve_reference_video(assets)
    source_videos = _resolve_source_videos(assets)
    existing_experience_path = _resolve_workspace_experience_path(workspace)

    if reference_video is None and existing_experience_path is None:
        raise ValueError("Reference video or existing reference analysis is required to create a styled video.")
    if not source_videos:
        raise ValueError("At least one source video is required to create a styled video.")
    if len(source_videos) > 10:
        source_videos = source_videos[:10]

    run = _build_run_layout(
        workspace_id=workspace.get("workspace_id") or "workspace_unknown",
        conversation_id=conversation_id,
        reference_video=reference_video,
        source_videos=source_videos,
        workspace_folder=workspace.get("workspace_folder_path"),
    )

    if reference_video is not None and existing_experience_path is None:
        _run_ai4video_pipeline(reference_video, run.reference_output_dir)
    for video_path, output_dir in zip(source_videos, run.source_output_dirs):
        _run_ai4video_pipeline(video_path, output_dir)

    experience_path = existing_experience_path or run.reference_output_dir / "elastic_template.json"
    if not experience_path.exists():
        raise RuntimeError(f"Missing experience template: {experience_path}")
    external_audio_path = (
        run.external_audio_path
        if run.external_audio_path is not None and run.external_audio_path.exists()
        else _resolve_workspace_reference_audio_path(workspace)
    )

    planner_result = create_timeline_plan_with_llm(
        workspace_id=run.workspace_id,
        experience_path=experience_path,
        source_output_dirs=run.source_output_dirs,
        source_video_names=[path.name for path in source_videos],
        output_path=run.timeline_plan_path,
        planner_info_path=run.planner_info_path,
        user_instruction=user_instruction,
    )

    package_args = [
        _preferred_python_bin(),
        "-m",
        "app.tools.build_ai4video_package",
        "--materials",
        *[str(path) for path in run.source_output_dirs],
        "--videos",
        *[str(path) for path in source_videos],
        "--experience",
        str(experience_path),
        "--workspace-id",
        run.workspace_id,
        "--output",
        str(run.package_path),
        "--timeline-plan",
        str(planner_result.timeline_plan_path),
        "--planner-info",
        str(planner_result.planner_info_path),
    ]
    _run_command(package_args, cwd=_ai_service_dir())

    render_args = [
        _preferred_python_bin(),
        "-m",
        "app.tools.render_native_video",
        "--package",
        str(run.package_path),
        "--output",
        str(run.render_output_path),
        "--max-long-side",
        "1280",
        "--audio-mode",
        "external" if external_audio_path else "source",
        "--burn-subtitles",
        "--subtitle-font-size",
        "32",
        "--subtitle-font-name",
        "Heiti SC",
        "--preset",
        "veryfast",
        "--crf",
        "26",
    ]
    ffmpeg_full = Path("/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg")
    if ffmpeg_full.exists():
        render_args.extend(["--ffmpeg-bin", str(ffmpeg_full)])
    if external_audio_path:
        render_args.extend(["--external-audio-path", str(external_audio_path)])
    _run_command(render_args, cwd=_ai_service_dir())

    return {
        "workflow": "CREATE_STYLED_VIDEO",
        "workspaceId": run.workspace_id,
        "referenceVideoPath": str(run.reference_video) if run.reference_video else None,
        "sourceVideoPaths": [str(path) for path in run.source_videos],
        "referenceOutputDir": str(run.reference_output_dir),
        "sourceOutputDirs": [str(path) for path in run.source_output_dirs],
        "experiencePath": str(experience_path),
        "timelinePlanPath": str(planner_result.timeline_plan_path),
        "plannerInfoPath": str(planner_result.planner_info_path),
        "plannerProvider": planner_result.provider,
        "plannerModel": planner_result.model,
        "selectedVideoClipCount": planner_result.selected_video_clip_count,
        "targetDurationMs": planner_result.target_duration_ms,
        "packagePath": str(run.package_path),
        "renderOutputPath": str(run.render_output_path),
        "renderResultPath": str(run.render_result_path),
        "externalAudioPath": str(external_audio_path) if external_audio_path else None,
    }


def _build_run_layout(
    *,
    workspace_id: str,
    conversation_id: str,
    reference_video: Path | None,
    source_videos: list[Path],
    workspace_folder: Any = None,
) -> StyledVideoRun:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_slug = f"{_slugify(conversation_id)}_{timestamp}"
    run_root = _repo_root() / "ai-service" / "output" / "im-runs" / _slugify(workspace_id) / run_slug
    analysis_root = run_root / "analysis"
    workspace_root = _resolve_workspace_root(workspace_folder)
    if workspace_root is not None:
        plans_root = workspace_root / "artifacts" / "plans"
        renders_root = workspace_root / "artifacts" / "renders"
    else:
        plans_root = run_root / "plans"
        renders_root = run_root / "renders"
    analysis_root.mkdir(parents=True, exist_ok=True)
    plans_root.mkdir(parents=True, exist_ok=True)
    renders_root.mkdir(parents=True, exist_ok=True)

    reference_output_dir = analysis_root / (
        f"reference_{_slugify(reference_video.stem)}" if reference_video else "reference_existing_analysis"
    )
    source_output_dirs = [
        analysis_root / f"source_{index:02d}_{_slugify(video_path.stem)}"
        for index, video_path in enumerate(source_videos, start=1)
    ]
    timeline_plan_path = plans_root / f"{run_slug}.timeline_plan.json"
    planner_info_path = plans_root / f"{run_slug}.planner-info.json"
    package_path = plans_root / f"{run_slug}.editing-package.json"
    render_output_path = renders_root / f"{run_slug}.native.final.mp4"
    render_result_path = render_output_path.with_suffix(".render-result.json")
    external_audio_path = (
        reference_output_dir / f"{reference_video.stem}.wav" if reference_video is not None else None
    )

    return StyledVideoRun(
        workspace_id=workspace_id,
        reference_video=reference_video,
        source_videos=source_videos,
        reference_output_dir=reference_output_dir,
        source_output_dirs=source_output_dirs,
        timeline_plan_path=timeline_plan_path,
        planner_info_path=planner_info_path,
        package_path=package_path,
        render_output_path=render_output_path,
        render_result_path=render_result_path,
        external_audio_path=external_audio_path,
    )


def _resolve_workspace_root(workspace_folder: Any) -> Path | None:
    if not isinstance(workspace_folder, str) or not workspace_folder.strip():
        return None
    workspace_root = Path(workspace_folder).expanduser().resolve()
    return workspace_root if workspace_root.exists() else None


def _run_ai4video_pipeline(video_path: Path, output_dir: Path) -> None:
    elastic_template = output_dir / "elastic_template.json"
    if elastic_template.exists():
        return

    args = [
        _preferred_python_bin(),
        str(_repo_root() / "AI4Video" / "pipeline_api.py"),
        str(video_path),
        "--output-dir",
        str(output_dir),
    ]
    _run_command(args, cwd=_repo_root())


def _run_command(args: list[str], *, cwd: Path) -> None:
    env = os.environ.copy()
    for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
        env.pop(key, None)

    completed = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Command failed with exit code "
            f"{completed.returncode}: {' '.join(args)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )


def _resolve_reference_video(assets: dict[str, Any]) -> Path | None:
    reference_video = assets.get("reference_video") or {}
    return _resolve_video_path(reference_video)


def _resolve_workspace_experience_path(workspace: dict[str, Any]) -> Path | None:
    workspace_folder = workspace.get("workspace_folder_path")
    if not workspace_folder:
        return None

    template_path = (
        Path(str(workspace_folder)).expanduser().resolve()
        / "assets"
        / "template"
        / "elastic_template.json"
    )
    if template_path.exists():
        return template_path
    return None


def _resolve_workspace_reference_audio_path(workspace: dict[str, Any]) -> Path | None:
    workspace_folder = workspace.get("workspace_folder_path")
    if not workspace_folder:
        return None

    intermediate_dir = (
        Path(str(workspace_folder)).expanduser().resolve()
        / "assets"
        / "intermediate"
    )
    if not intermediate_dir.exists():
        return None

    wav_candidates = sorted(
        intermediate_dir.glob("*.wav"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return wav_candidates[0] if wav_candidates else None


def _resolve_source_videos(assets: dict[str, Any]) -> list[Path]:
    source_videos = assets.get("source_videos") or []
    resolved = [_resolve_video_path(item) for item in source_videos]
    paths = [path for path in resolved if path is not None]
    if paths:
        return paths

    selected = _resolve_video_path(assets.get("selected_source_video") or {})
    return [selected] if selected else []


def _resolve_video_path(asset: dict[str, Any]) -> Path | None:
    raw_path = asset.get("workspace_file_path") or asset.get("workspace_relative_path")
    if not raw_path:
        return None

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = _repo_root() / path
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Video file not found: {resolved}")
    return resolved


def _repo_root() -> Path:
    configured = os.environ.get("CAPCUTAI_REPO_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()

    return Path(__file__).resolve().parents[3]


def _ai_service_dir() -> Path:
    return _repo_root() / "ai-service"


def _slugify(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    compact = "-".join(part for part in normalized.split("-") if part)
    return compact or "run"


def _preferred_python_bin() -> str:
    configured = os.environ.get("CAPCUTAI_PYTHON_BIN")
    if configured:
        return configured

    python_bin = shutil.which("python")
    if python_bin:
        return python_bin

    return sys.executable
