import json
import math
import os
import subprocess
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


JsonDict = dict[str, Any]


def load_editor_export_package(package_path: Path) -> JsonDict:
    return json.loads(package_path.read_text(encoding="utf-8"))


def build_hyperframes_composition_draft(export_package: JsonDict) -> JsonDict:
    timeline_plan = export_package["timelinePlan"]
    editing_job = export_package["editingJob"]
    source_assets = export_package.get("sourceAssets", [])
    source_materials = export_package.get("sourceMaterials", [])
    resolved_dimensions = _resolve_render_dimensions(export_package)

    asset_by_id = {asset["assetId"]: asset for asset in source_assets}
    source_material_by_id = {
        source_material["sourceMaterialId"]: source_material for source_material in source_materials
    }
    subtitle_clips = _get_track_clips(timeline_plan, "subtitle")
    overlay_clips = _get_track_clips(timeline_plan, "overlay")
    audio_clips = _get_track_clips(timeline_plan, "audio")
    video_clips = _get_track_clips(timeline_plan, "video")

    scenes = []

    for scene_index, video_clip in enumerate(video_clips, start=1):
        asset = asset_by_id.get(video_clip.get("assetId", ""))
        source_material_id = video_clip.get("sourceMaterialId", "unknown_source_material")
        source_material = source_material_by_id.get(source_material_id, {})
        preview_image_path = _find_preview_image_path(
            source_material.get("sourceCaseId"),
            video_clip.get("sourceStartMs", 0),
        )
        subtitle_texts = _find_overlapping_labels(video_clip, subtitle_clips)
        overlay_texts = _find_overlapping_labels(video_clip, overlay_clips)
        audio_cue_labels = _find_overlapping_labels(video_clip, audio_clips)

        scenes.append(
            {
                "sceneId": f"scene_{scene_index}",
                "assetId": video_clip.get("assetId", "unknown_asset"),
                "sourceMaterialId": source_material_id,
                "assetName": asset["name"] if asset else "Unknown asset",
                "assetObjectUrl": asset.get("objectUrl") if asset else None,
                "sourceVideoPath": _find_source_video_path(source_material.get("sourceCaseId")),
                "previewImagePath": str(preview_image_path) if preview_image_path else None,
                "timelineStartMs": video_clip.get("startMs", 0),
                "durationMs": video_clip.get("durationMs", 0),
                "sourceStartMs": video_clip.get("sourceStartMs", 0),
                "label": video_clip.get("label", ""),
                "subtitleTexts": subtitle_texts,
                "overlayTexts": overlay_texts,
                "audioCueLabels": audio_cue_labels,
            }
        )

    unresolved_asset_names = [
        asset["name"] for asset in source_assets if not _has_stable_local_source(asset)
    ]
    warnings = []

    if unresolved_asset_names:
        warnings.append(
            "Source assets still use browser object URLs or missing file paths: "
            + ", ".join(unresolved_asset_names)
        )

    if not scenes:
        warnings.append("No video scenes were generated from timelinePlan.tracks[].clips.")

    fps = editing_job["renderHints"]["fps"]
    duration_ms = timeline_plan["targetDurationMs"]

    return {
        "compositionId": f"hyperframes_{timeline_plan['timelineId']}",
        "timelineId": timeline_plan["timelineId"],
        "renderer": "hyperframes",
        "durationMs": duration_ms,
        "fps": fps,
        "width": resolved_dimensions["width"],
        "height": resolved_dimensions["height"],
        "totalFrames": max(1, math.ceil(duration_ms / 1000 * fps)),
        "scenes": scenes,
        "warnings": warnings,
    }


def write_hyperframes_draft_bundle(
    export_package: JsonDict,
    draft: JsonDict,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    video_assets = _materialize_source_videos(draft, assets_dir)
    _materialize_preview_images(draft, assets_dir)

    draft_json = output_dir / "composition.draft.json"
    timeline_plan_json = output_dir / "timeline-plan.json"
    editing_job_json = output_dir / "editing-job.json"
    render_result_json = output_dir / "render-result.json"
    preview_data_js = output_dir / "preview-data.js"
    preview_js = output_dir / "preview.js"
    preview_html = output_dir / "preview.html"
    composition_html = output_dir / "index.html"
    package_json = output_dir / "package.json"
    hyperframes_json = output_dir / "hyperframes.json"
    meta_json = output_dir / "meta.json"
    readme_md = output_dir / "README.md"

    draft_json.write_text(_dump_json(draft), encoding="utf-8")
    timeline_plan_json.write_text(_dump_json(export_package["timelinePlan"]), encoding="utf-8")
    editing_job_json.write_text(_dump_json(export_package["editingJob"]), encoding="utf-8")
    render_result_json.write_text(_dump_json(export_package["renderResult"]), encoding="utf-8")
    preview_data_js.write_text(_build_composition_data_js(draft), encoding="utf-8")
    preview_js.write_text(_build_composition_js(), encoding="utf-8")
    preview_html.write_text(_build_preview_html(draft), encoding="utf-8")
    composition_html.write_text(
        _build_render_composition_html(export_package, draft, video_assets), encoding="utf-8"
    )
    package_json.write_text(_build_hyperframes_package_json(output_dir.name), encoding="utf-8")
    hyperframes_json.write_text(_build_hyperframes_config_json(), encoding="utf-8")
    meta_json.write_text(_build_hyperframes_meta_json(output_dir.name), encoding="utf-8")
    readme_md.write_text(_build_bundle_readme(export_package, draft, output_dir), encoding="utf-8")

    return {
        "draft_json": draft_json,
        "timeline_plan_json": timeline_plan_json,
        "editing_job_json": editing_job_json,
        "render_result_json": render_result_json,
        "preview_data_js": preview_data_js,
        "preview_js": preview_js,
        "preview_html": preview_html,
        "composition_html": composition_html,
        "package_json": package_json,
        "hyperframes_json": hyperframes_json,
        "meta_json": meta_json,
        "readme_md": readme_md,
    }


def render_hyperframes_bundle(
    bundle_dir: Path,
    output_path: Optional[Path] = None,
    quality: str = "draft",
    fps: Optional[int] = None,
    use_docker: bool = False,
) -> JsonDict:
    editing_job = json.loads((bundle_dir / "editing-job.json").read_text(encoding="utf-8"))
    render_result_path = bundle_dir / "render-result.json"
    render_result = json.loads(render_result_path.read_text(encoding="utf-8"))
    resolved_output_path = output_path or Path(editing_job["outputPath"]).expanduser().resolve()
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

    lint_command = ["npx", "--yes", "hyperframes", "lint", str(bundle_dir)]
    lint_process = subprocess.run(
        lint_command,
        capture_output=True,
        text=True,
        cwd=bundle_dir,
        check=False,
    )
    if lint_process.returncode != 0:
        render_result["status"] = "failed"
        render_result["errorMessage"] = (lint_process.stderr or lint_process.stdout).strip()
        render_result_path.write_text(_dump_json(render_result), encoding="utf-8")
        raise RuntimeError(f"HyperFrames lint failed: {render_result['errorMessage']}")

    render_command = [
        "npx",
        "--yes",
        "hyperframes",
        "render",
        str(bundle_dir),
        "--composition",
        "index.html",
        "--quality",
        quality,
        "--output",
        str(resolved_output_path),
    ]
    if use_docker:
        render_command.append("--docker")
    else:
        render_command.extend(
            [
                "--workers",
                "1",
                "--no-browser-gpu",
            ]
        )
    if fps:
        render_command.extend(["--fps", str(fps)])

    command_env = None
    if use_docker:
        command_env = {**os.environ, "DOCKER_BUILDKIT": "0"}

    render_process = subprocess.run(
        render_command,
        capture_output=True,
        text=True,
        cwd=bundle_dir,
        env=command_env,
        check=False,
    )
    if render_process.returncode != 0:
        render_result["status"] = "failed"
        render_result["errorMessage"] = (render_process.stderr or render_process.stdout).strip()
        render_result_path.write_text(_dump_json(render_result), encoding="utf-8")
        raise RuntimeError(f"HyperFrames render failed: {render_result['errorMessage']}")

    render_result["status"] = "completed"
    render_result["outputPath"] = str(resolved_output_path)
    render_result.pop("errorMessage", None)
    render_result_path.write_text(_dump_json(render_result), encoding="utf-8")

    return {
        "outputPath": str(resolved_output_path),
        "stdout": render_process.stdout.strip(),
        "stderr": render_process.stderr.strip(),
        "renderResultPath": str(render_result_path),
    }


def _dump_json(payload: JsonDict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _get_track_clips(timeline_plan: JsonDict, track_type: str) -> list[JsonDict]:
    for track in timeline_plan.get("tracks", []):
        if track.get("type") == track_type:
            return sorted(track.get("clips", []), key=lambda clip: clip.get("startMs", 0))
    return []


def _find_overlapping_labels(base_clip: JsonDict, candidate_clips: list[JsonDict]) -> list[str]:
    base_start_ms = base_clip.get("startMs", 0)
    base_end_ms = base_start_ms + base_clip.get("durationMs", 0)
    labels = []

    for candidate in candidate_clips:
        candidate_start_ms = candidate.get("startMs", 0)
        candidate_end_ms = candidate_start_ms + candidate.get("durationMs", 0)
        overlaps = candidate_start_ms < base_end_ms and candidate_end_ms > base_start_ms
        if overlaps and candidate.get("label"):
            labels.append(candidate["label"])

    return labels


def _has_stable_local_source(asset: JsonDict) -> bool:
    object_url = asset.get("objectUrl")
    if not object_url:
        return False
    return not str(object_url).startswith("blob:")


def _build_composition_data_js(draft: JsonDict) -> str:
    payload = json.dumps(draft, indent=2, ensure_ascii=False)
    return f"window.__CAPCUTAI_HYPERFRAMES_DRAFT__ = {payload};\n"


def _build_composition_js() -> str:
    return """const draft = window.__CAPCUTAI_HYPERFRAMES_DRAFT__;

const stage = document.querySelector("[data-stage]");
const meta = document.querySelector("[data-meta]");
const sceneLabel = document.querySelector("[data-scene-label]");
const sceneAsset = document.querySelector("[data-scene-asset]");
const sceneTime = document.querySelector("[data-scene-time]");
const sceneSubtitles = document.querySelector("[data-scene-subtitles]");
const sceneOverlays = document.querySelector("[data-scene-overlays]");
const sceneAudio = document.querySelector("[data-scene-audio]");
const warningList = document.querySelector("[data-warning-list]");

if (!draft || !stage) {
  throw new Error("Missing HyperFrames draft payload.");
}

meta.textContent = `${draft.width}x${draft.height} · ${draft.fps}fps · ${draft.totalFrames} frames`;

if (draft.warnings.length > 0) {
  warningList.innerHTML = "";
  draft.warnings.forEach((warning) => {
    const item = document.createElement("li");
    item.textContent = warning;
    warningList.appendChild(item);
  });
}

const durationMs = Math.max(1, draft.durationMs);
const sceneCount = Math.max(1, draft.scenes.length);
const startedAt = performance.now();

function render(now) {
  const elapsed = (now - startedAt) % durationMs;
  const scene = draft.scenes.find((entry) => {
    const sceneEnd = entry.timelineStartMs + entry.durationMs;
    return elapsed >= entry.timelineStartMs && elapsed < sceneEnd;
  }) || draft.scenes[Math.min(sceneCount - 1, 0)];

  if (scene) {
    sceneLabel.textContent = scene.label;
    sceneAsset.textContent = `${scene.assetName} · ${scene.sourceMaterialId}`;
    sceneTime.textContent = `${Math.round(scene.timelineStartMs / 1000)}s -> ${Math.round((scene.timelineStartMs + scene.durationMs) / 1000)}s`;
    sceneSubtitles.textContent = scene.subtitleTexts.join(" / ") || "No subtitles";
    sceneOverlays.textContent = scene.overlayTexts.join(" / ") || "No overlays";
    sceneAudio.textContent = scene.audioCueLabels.join(" / ") || "No audio cues";
    stage.style.setProperty("--scene-progress", String(elapsed / durationMs));
    const previewPath = scene.previewImagePath ? `url("${scene.previewImagePath}")` : "none";
    stage.style.setProperty("--scene-image", previewPath);
  } else {
    sceneLabel.textContent = "No scenes";
  }

  requestAnimationFrame(render);
}

requestAnimationFrame(render);
"""


def _build_preview_html(draft: JsonDict) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{draft["compositionId"]}</title>
    <style>
      :root {{
        color-scheme: dark;
        --panel: rgba(16, 19, 22, 0.84);
        --line: rgba(255, 255, 255, 0.12);
        --scene-progress: 0;
        --scene-image: none;
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background:
          radial-gradient(circle at top, rgba(88, 166, 255, 0.18), transparent 22%),
          #0a0c0e;
        color: #f3f5f7;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }}

      .shell {{
        width: min(92vw, 1240px);
        display: grid;
        grid-template-columns: minmax(0, 1fr) 320px;
        gap: 18px;
      }}

      .stage {{
        min-height: 720px;
        border-radius: 16px;
        border: 1px solid var(--line);
        background:
          linear-gradient(160deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)),
          rgba(9, 11, 13, 0.94);
        padding: 18px;
        display: grid;
        grid-template-rows: auto 1fr auto;
        overflow: hidden;
      }}

      .eyebrow {{
        font-size: 12px;
        letter-spacing: 0;
        text-transform: uppercase;
        color: #9aa7b4;
      }}

      .meta {{
        margin-top: 8px;
        font-size: 14px;
        color: #dce5ee;
      }}

      .preview {{
        align-self: center;
        justify-self: center;
        width: min(100%, 420px);
        aspect-ratio: 9 / 16;
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,0.08);
        background:
          var(--scene-image) center / cover no-repeat,
          linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02)),
          linear-gradient(180deg, rgba(88,166,255,0.12), rgba(0,0,0,0));
        padding: 18px;
        display: grid;
        align-content: space-between;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03);
      }}

      .scene-title {{
        font-size: 28px;
        line-height: 1.15;
        font-weight: 700;
      }}

      .scene-sub {{
        margin-top: 10px;
        font-size: 14px;
        color: #c8d2dd;
      }}

      .caption {{
        border-radius: 12px;
        background: rgba(9, 11, 13, 0.76);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 12px;
        font-size: 15px;
        line-height: 1.45;
      }}

      .sidebar {{
        border-radius: 16px;
        border: 1px solid var(--line);
        background: var(--panel);
        padding: 16px;
        display: grid;
        align-content: start;
        gap: 14px;
      }}

      .card {{
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.06);
        background: rgba(255,255,255,0.03);
        padding: 12px;
      }}

      .card h2 {{
        margin: 0 0 8px;
        font-size: 13px;
        font-weight: 600;
        color: #9aa7b4;
      }}

      .card p,
      .card li {{
        margin: 0;
        font-size: 13px;
        line-height: 1.5;
        color: #f3f5f7;
        word-break: break-word;
      }}

      ul {{
        margin: 0;
        padding-left: 18px;
      }}

      @media (max-width: 960px) {{
        .shell {{
          grid-template-columns: minmax(0, 1fr);
        }}
      }}
    </style>
  </head>
  <body>
    <div class="shell">
      <main class="stage" data-stage>
        <div>
          <div class="eyebrow">HyperFrames Composition Draft</div>
          <div class="meta" data-meta></div>
        </div>
        <div class="preview">
          <div>
            <div class="scene-title" data-scene-label>Loading scene...</div>
            <div class="scene-sub" data-scene-asset></div>
            <div class="scene-sub" data-scene-time></div>
          </div>
          <div class="caption" data-scene-subtitles></div>
        </div>
        <div class="eyebrow">Preview draft only. Real render still needs stable local file paths.</div>
      </main>
      <aside class="sidebar">
        <div class="card">
          <h2>Overlays</h2>
          <p data-scene-overlays>No overlays</p>
        </div>
        <div class="card">
          <h2>Audio Cues</h2>
          <p data-scene-audio>No audio cues</p>
        </div>
        <div class="card">
          <h2>Warnings</h2>
          <ul data-warning-list>
            <li>No warnings</li>
          </ul>
        </div>
      </aside>
    </div>
    <script src="./composition-data.js"></script>
    <script src="./preview.js"></script>
  </body>
</html>
"""


def _build_render_composition_html(
    export_package: JsonDict,
    draft: JsonDict,
    video_assets: dict[str, JsonDict],
) -> str:
    duration_seconds = _seconds(draft["durationMs"])
    width = draft["width"]
    height = draft["height"]

    scene_elements = []
    for scene_index, scene in enumerate(draft.get("scenes", []), start=1):
        base_track_index = scene_index * 10
        scene_video = video_assets.get(scene.get("sourceMaterialId", ""))
        preview_image_path = scene.get("previewImagePath")
        if scene_video:
            scene_elements.append(
                f"""<video
      id="{_escape_html(scene['sceneId'])}-image"
      class="clip scene-image"
      src="{_escape_html(scene_video['relativePath'])}"
      data-start="{_seconds(scene['timelineStartMs'])}"
      data-duration="{_seconds(scene['durationMs'])}"
      data-media-start="{_seconds(scene.get('sourceStartMs', 0))}"
      data-track-index="{base_track_index}"
      playsinline
      preload="auto"
      muted
    ></video>"""
            )
        elif preview_image_path:
            scene_elements.append(
                f"""<img
      id="{_escape_html(scene['sceneId'])}-image"
      class="clip scene-image"
      src="{_escape_html(preview_image_path)}"
      alt="{_escape_html(scene.get('label', 'scene'))}"
      data-start="{_seconds(scene['timelineStartMs'])}"
      data-duration="{_seconds(scene['durationMs'])}"
      data-track-index="{base_track_index}"
    />"""
            )

        scene_elements.append(
            f"""<div
      id="{_escape_html(scene['sceneId'])}-gradient"
      class="clip scene-gradient"
      data-start="{_seconds(scene['timelineStartMs'])}"
      data-duration="{_seconds(scene['durationMs'])}"
      data-track-index="{base_track_index + 1}"
    ></div>"""
        )

        scene_elements.append(
            f"""<div
      id="{_escape_html(scene['sceneId'])}-label"
      class="clip scene-label"
      data-start="{_seconds(scene['timelineStartMs'])}"
      data-duration="{_seconds(scene['durationMs'])}"
      data-track-index="{base_track_index + 2}"
    >{_escape_html(scene.get("label", ""))}</div>"""
        )

        if scene.get("overlayTexts"):
            scene_elements.append(
                f"""<div
      id="{_escape_html(scene['sceneId'])}-overlay"
      class="clip scene-overlay"
      data-start="{_seconds(scene['timelineStartMs'])}"
      data-duration="{_seconds(scene['durationMs'])}"
      data-track-index="{base_track_index + 3}"
    >{_escape_html(" / ".join(scene["overlayTexts"]))}</div>"""
            )

        subtitle_text = " / ".join(scene.get("subtitleTexts", []))
        if subtitle_text:
            scene_elements.append(
                f"""<div
      id="{_escape_html(scene['sceneId'])}-subtitle"
      class="clip scene-subtitle"
      data-start="{_seconds(scene['timelineStartMs'])}"
      data-duration="{_seconds(scene['durationMs'])}"
      data-track-index="{base_track_index + 4}"
    >{_escape_html(subtitle_text)}</div>"""
            )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={width}, height={height}" />
    <style>
      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}

      html,
      body {{
        width: {width}px;
        height: {height}px;
        overflow: hidden;
        background: #05070a;
        font-family: Arial, sans-serif;
      }}

      #root {{
        position: relative;
        width: {width}px;
        height: {height}px;
        overflow: hidden;
        background:
          radial-gradient(circle at top, rgba(88, 166, 255, 0.16), transparent 20%),
          #05070a;
      }}

      .clip {{
        position: absolute;
      }}

      .scene-image,
      .scene-gradient {{
        inset: 0;
        width: 100%;
        height: 100%;
      }}

      .scene-image {{
        object-fit: contain;
        background: #000;
      }}

      .scene-gradient {{
        background:
          linear-gradient(180deg, rgba(5, 7, 10, 0.14), rgba(5, 7, 10, 0.78)),
          radial-gradient(circle at top, rgba(88, 166, 255, 0.12), transparent 36%);
      }}

      .scene-label {{
        left: 48px;
        right: 48px;
        top: 64px;
        color: #f3f5f7;
        font-size: 42px;
        line-height: 1.18;
        font-weight: 700;
        text-shadow: 0 8px 26px rgba(0, 0, 0, 0.38);
      }}

      .scene-overlay {{
        left: 48px;
        top: 148px;
        max-width: 760px;
        color: #dfe8f2;
        font-size: 20px;
        line-height: 1.45;
        padding: 12px 16px;
        border-radius: 12px;
        background: rgba(8, 10, 12, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
      }}

      .scene-subtitle {{
        left: 48px;
        right: 48px;
        bottom: 88px;
        color: #ffffff;
        font-size: 28px;
        line-height: 1.35;
        font-weight: 600;
        text-align: center;
        padding: 14px 20px;
        border-radius: 14px;
        background: rgba(5, 7, 10, 0.72);
        border: 1px solid rgba(255, 255, 255, 0.08);
      }}
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="main"
      data-start="0"
      data-duration="{duration_seconds}"
      data-width="{width}"
      data-height="{height}"
    >
      {' '.join(scene_elements)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = window.__timelines["main"] || {{}};
    </script>
  </body>
</html>
"""


def _build_bundle_readme(export_package: JsonDict, draft: JsonDict, output_dir: Path) -> str:
    warning_lines = "\n".join(f"- {warning}" for warning in draft.get("warnings", [])) or "- No warnings"
    return f"""# HyperFrames Draft Bundle

This directory is the local-first handoff between the editor export package and a future HyperFrames render step.

## Source

- Timeline: `{export_package["timelinePlan"]["timelineId"]}`
- Job: `{export_package["editingJob"]["jobId"]}`
- Output directory: `{output_dir}`

## Files

- `composition.draft.json`
- `timeline-plan.json`
- `editing-job.json`
- `render-result.json`
- `index.html`
- `preview.html`
- `preview-data.js`
- `preview.js`
- `hyperframes.json`
- `package.json`
- `meta.json`

## Current warnings

{warning_lines}

## Important limitation

The current draft uses browser asset metadata from the editor export package. If the source assets only contain `blob:` object URLs, HyperFrames still cannot render a final MP4 directly.

Before real render, replace browser-only URLs with stable local file paths or workspace-managed asset paths.
"""


def _materialize_preview_images(draft: JsonDict, assets_dir: Path) -> None:
    for scene in draft.get("scenes", []):
        preview_image_path = scene.get("previewImagePath")
        if not preview_image_path:
            continue

        source_path = Path(preview_image_path)
        if not source_path.exists():
            continue

        target_name = f"{scene['sceneId']}{source_path.suffix.lower() or '.jpg'}"
        target_path = assets_dir / target_name
        shutil.copyfile(source_path, target_path)
        scene["previewImagePath"] = f"./assets/{target_name}"


def _find_preview_image_path(source_case_id: Optional[str], source_start_ms: int) -> Optional[Path]:
    if not source_case_id:
        return None

    keyframes_dir = Path(__file__).resolve().parents[3] / "data" / "test_case" / source_case_id / "keyframes"
    if not keyframes_dir.exists():
        return None

    candidates = []
    for file_path in keyframes_dir.iterdir():
        if not file_path.is_file():
            continue

        match = re.search(r"_(\d+)ms", file_path.name)
        if not match:
            continue

        candidates.append((abs(int(match.group(1)) - int(source_start_ms)), int(match.group(1)), file_path))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2]


def _materialize_source_videos(draft: JsonDict, assets_dir: Path) -> dict[str, JsonDict]:
    video_assets: dict[str, JsonDict] = {}

    for scene in draft.get("scenes", []):
        source_material_id = scene.get("sourceMaterialId")
        source_video_path = scene.get("sourceVideoPath")
        if not source_material_id or not source_video_path or source_material_id in video_assets:
            continue

        source_path = Path(str(source_video_path))
        if not source_path.exists():
            continue

        target_name = f"{source_material_id}{source_path.suffix.lower() or '.mp4'}"
        target_path = assets_dir / target_name
        shutil.copyfile(source_path, target_path)
        video_assets[source_material_id] = {
            "relativePath": f"./assets/{target_name}",
            "path": str(target_path),
        }

    return video_assets


def _build_hyperframes_package_json(name: str) -> str:
    payload = {
        "name": name,
        "private": True,
        "type": "module",
        "scripts": {
            "dev": "npx --yes hyperframes@0.6.63 preview",
            "check": "npx --yes hyperframes@0.6.63 lint",
            "render": "npx --yes hyperframes@0.6.63 render",
        },
    }
    return _dump_json(payload)


def _build_hyperframes_config_json() -> str:
    payload = {
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
    }
    return _dump_json(payload)


def _build_hyperframes_meta_json(name: str) -> str:
    payload = {"id": name, "name": name, "createdAt": datetime.now(timezone.utc).isoformat()}
    return _dump_json(payload)


def _seconds(value_ms: int) -> str:
    return f"{max(0, value_ms) / 1000:.3f}"


def _resolve_render_dimensions(export_package: JsonDict) -> JsonDict:
    for source_material in export_package.get("sourceMaterials", []):
        source_video_path = _find_source_video_path(source_material.get("sourceCaseId"))
        if not source_video_path:
            continue

        probed = _probe_video_dimensions(source_video_path)
        if probed:
            return _fit_render_dimensions(probed["width"], probed["height"])

    render_hints = export_package.get("editingJob", {}).get("renderHints", {})
    return _fit_render_dimensions(
        int(render_hints.get("width", 1080)),
        int(render_hints.get("height", 1920)),
    )


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


def _probe_video_dimensions(video_path: str) -> Optional[JsonDict]:
    command = [
        "ffprobe",
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


def _fit_render_dimensions(width: int, height: int, max_long_side: int = 640) -> JsonDict:
    width = max(1, int(width))
    height = max(1, int(height))
    long_side = max(width, height)
    if long_side <= max_long_side:
        return {"width": width, "height": height}

    scale = max_long_side / long_side
    scaled_width = max(2, int(round(width * scale)))
    scaled_height = max(2, int(round(height * scale)))

    if scaled_width % 2 != 0:
        scaled_width -= 1
    if scaled_height % 2 != 0:
        scaled_height -= 1

    return {"width": scaled_width, "height": scaled_height}


def _escape_html(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
