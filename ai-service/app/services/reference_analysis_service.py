from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.styled_video_service import _repo_root, _run_ai4video_pipeline, _slugify


def analyze_reference_video_from_workspace(
    workspace: dict[str, Any],
    assets: dict[str, Any],
    *,
    conversation_id: str,
) -> dict[str, Any]:
    reference_video = _resolve_reference_video(assets)
    if reference_video is None:
        raise ValueError("Reference video is required to analyze reference style.")

    workspace_id = workspace.get("workspace_id") or "workspace_unknown"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_slug = f"{_slugify(conversation_id)}_{timestamp}"
    internal_output_dir = (
        _repo_root()
        / "ai-service"
        / "output"
        / "im-runs"
        / _slugify(workspace_id)
        / run_slug
        / "analysis"
        / f"reference_{_slugify(reference_video.stem)}"
    )
    workspace_exports = _prepare_workspace_outputs(
        workspace=workspace,
        reference_video=reference_video,
    )
    output_dir = workspace_exports["intermediate_dir"]

    _run_ai4video_pipeline(reference_video, output_dir)

    elastic_template_path = output_dir / "elastic_template.json"
    if not elastic_template_path.exists():
        raise RuntimeError(f"Missing elastic template: {elastic_template_path}")

    _finalize_workspace_outputs(
        output_dir=output_dir,
        workspace_exports=workspace_exports,
    )
    _archive_reference_outputs(
        output_dir=output_dir,
        archive_dir=internal_output_dir,
    )

    elastic_template = json.loads(elastic_template_path.read_text(encoding="utf-8"))
    style_metadata = elastic_template.get("style_metadata", {})
    storyline_structure = elastic_template.get("storyline_structure", [])
    dynamic_pacing_blueprint = elastic_template.get("dynamic_pacing_blueprint", [])

    return {
        "workflow": "ANALYZE_REFERENCE",
        "workspaceId": workspace_id,
        "referenceVideoPath": str(reference_video),
        "outputDir": str(workspace_exports["intermediate_dir"]),
        "elasticTemplatePath": str(workspace_exports["elastic_template_path"]),
        "step1AudioPath": str(workspace_exports["step1_audio_path"]),
        "step2TranscriptPath": str(workspace_exports["step2_transcript_path"]),
        "step3VisualPath": str(workspace_exports["step3_visual_path"]),
        "internalOutputDir": str(internal_output_dir),
        "internalElasticTemplatePath": str(internal_output_dir / "elastic_template.json"),
        "styleId": style_metadata.get("style_id"),
        "category": style_metadata.get("category"),
        "pacingStyle": style_metadata.get("pacing_style"),
        "visualTheme": style_metadata.get("visual_theme"),
        "storylinePhaseCount": len(storyline_structure),
        "dynamicBeatCount": len(dynamic_pacing_blueprint),
        "sampleVideoDurationMs": style_metadata.get("sample_video_total_duration_ms"),
    }


def _resolve_reference_video(assets: dict[str, Any]) -> Path | None:
    reference_video = assets.get("reference_video") or {}
    raw_path = reference_video.get("workspace_file_path") or reference_video.get("workspace_relative_path")
    if not raw_path:
        return None

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = _repo_root() / path
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Reference video not found: {resolved}")
    return resolved


def _prepare_workspace_outputs(
    *,
    workspace: dict[str, Any],
    reference_video: Path,
) -> dict[str, Path]:
    workspace_folder = _resolve_workspace_folder(workspace, reference_video)
    template_dir = workspace_folder / "assets" / "template"
    intermediate_dir = workspace_folder / "assets" / "intermediate"
    template_dir.mkdir(parents=True, exist_ok=True)
    intermediate_dir.mkdir(parents=True, exist_ok=True)

    # Clear stale marker files so UI progress reflects the current run, not a prior analysis.
    for path in [
        template_dir / "elastic_template.json",
        intermediate_dir / "elastic_template.json",
        intermediate_dir / "step1_audio.json",
        intermediate_dir / "step2_transcript.json",
        intermediate_dir / "step3_visual.json",
    ]:
        if path.exists():
            path.unlink()

    elastic_template_path = template_dir / "elastic_template.json"
    step1_audio_path = intermediate_dir / "step1_audio.json"
    step2_transcript_path = intermediate_dir / "step2_transcript.json"
    step3_visual_path = intermediate_dir / "step3_visual.json"

    return {
        "template_dir": template_dir,
        "intermediate_dir": intermediate_dir,
        "elastic_template_path": elastic_template_path,
        "step1_audio_path": step1_audio_path,
        "step2_transcript_path": step2_transcript_path,
        "step3_visual_path": step3_visual_path,
    }


def _finalize_workspace_outputs(
    *,
    output_dir: Path,
    workspace_exports: dict[str, Path],
) -> None:
    _copy_required(
        output_dir / "elastic_template.json",
        workspace_exports["elastic_template_path"],
    )


def _archive_reference_outputs(*, output_dir: Path, archive_dir: Path) -> None:
    if archive_dir.exists():
        shutil.rmtree(archive_dir)
    shutil.copytree(output_dir, archive_dir)


def _resolve_workspace_folder(workspace: dict[str, Any], reference_video: Path) -> Path:
    raw_workspace_folder = workspace.get("workspace_folder_path")
    if raw_workspace_folder:
        return Path(str(raw_workspace_folder)).expanduser().resolve()

    current = reference_video.resolve()
    for parent in current.parents:
        if parent.name == "Workspaces":
            break
        if parent.parent.name == "Workspaces":
            return parent

    raise ValueError("Workspace folder path is required to export analysis outputs.")


def _copy_required(source: Path, destination: Path) -> None:
    if not source.exists():
        raise RuntimeError(f"Missing analysis output: {source}")
    shutil.copy2(source, destination)
