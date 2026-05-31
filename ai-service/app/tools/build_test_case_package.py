import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an editor export package directly from data/test_case mock inputs."
    )
    parser.add_argument(
        "--cases",
        nargs="+",
        required=True,
        help="One or more test case ids from data/test_case/<case_id>.",
    )
    parser.add_argument(
        "--workspace-id",
        default="workspace_test_case",
        help="Workspace id to embed in the package.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for the generated *.editing-package.json.",
    )
    parser.add_argument(
        "--max-video-clips-per-case",
        type=int,
        default=None,
        help="Optional cap for how many visual shots to keep per case.",
    )
    parser.add_argument(
        "--smoke-duration-ms",
        type=int,
        default=None,
        help="Optional cap for per-case smoke duration. Clips and subtitles outside this window are dropped.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    data_root = repo_root / "data"
    experience = _load_editing_experience(data_root / "elastic_template.json")

    source_materials = []
    source_assets = []
    timeline_tracks = {
        "video": {"trackId": "track_video_main", "type": "video", "clips": []},
        "subtitle": {"trackId": "track_caption_main", "type": "subtitle", "clips": []},
        "overlay": {"trackId": "track_overlay_main", "type": "overlay", "clips": []},
        "audio": {"trackId": "track_audio_main", "type": "audio", "clips": []},
    }

    cumulative_offset_ms = 0
    render_width = 1080
    render_height = 1920

    for material_index, case_id in enumerate(args.cases, start=1):
        case_dir = data_root / "test_case" / case_id
        source_material = _load_source_material(
            case_dir,
            case_id,
            max_video_clips_per_case=args.max_video_clips_per_case,
            smoke_duration_ms=args.smoke_duration_ms,
        )
        video_path = _find_case_video(case_dir)
        source_materials.append(source_material)

        width, height, duration_seconds, size_bytes = _probe_video(video_path)
        if material_index == 1 and width and height:
            render_width, render_height = width, height

        asset = {
            "assetId": f"asset_source_{material_index}",
            "workspaceId": args.workspace_id,
            "category": "VIDEO",
            "slot": "SOURCE",
            "origin": "DESKTOP",
            "storageMode": "LOCAL",
            "syncStatus": "READY",
            "name": video_path.name,
            "mimeType": "video/mp4",
            "sizeBytes": size_bytes,
            "addedAt": datetime.now(timezone.utc).isoformat(),
            "durationSeconds": duration_seconds,
            "frameWidth": width,
            "frameHeight": height,
            "objectUrl": str(video_path),
        }
        source_assets.append(asset)

        for shot_index, shot in enumerate(source_material["visualShots"], start=1):
            timeline_tracks["video"]["clips"].append(
                {
                    "clipId": f"clip_video_{material_index}_{shot_index}",
                    "assetId": asset["assetId"],
                    "sourceMaterialId": source_material["sourceMaterialId"],
                    "type": "video",
                    "startMs": cumulative_offset_ms + shot["startMs"],
                    "durationMs": max(1000, shot["endMs"] - shot["startMs"]),
                    "sourceStartMs": shot["startMs"],
                    "label": f"{asset['name']} · {shot['shotType']}",
                }
            )

        for sentence_index, sentence in enumerate(source_material["transcript"]["sentences"], start=1):
            timeline_tracks["subtitle"]["clips"].append(
                {
                    "clipId": f"clip_caption_{material_index}_{sentence_index}",
                    "sourceMaterialId": source_material["sourceMaterialId"],
                    "type": "subtitle",
                    "startMs": cumulative_offset_ms + sentence["startMs"],
                    "durationMs": max(400, sentence["endMs"] - sentence["startMs"]),
                    "label": sentence["text"],
                }
            )

        overlay_index = 0
        for shot in source_material["visualShots"]:
            if shot["editingUtility"] not in {"HOOK_OPENER", "EMPHASIS_HIGHLIGHT"}:
                continue
            overlay_index += 1
            timeline_tracks["overlay"]["clips"].append(
                {
                    "clipId": f"clip_overlay_{material_index}_{overlay_index}",
                    "sourceMaterialId": source_material["sourceMaterialId"],
                    "type": "overlay",
                    "startMs": cumulative_offset_ms + shot["startMs"],
                    "durationMs": max(1000, shot["endMs"] - shot["startMs"]),
                    "label": f"{case_id} · {shot['editingUtility']}",
                }
            )

        for drop_index, drop_ms in enumerate(source_material["dropsMs"], start=1):
            timeline_tracks["audio"]["clips"].append(
                {
                    "clipId": f"clip_audio_{material_index}_{drop_index}",
                    "sourceMaterialId": source_material["sourceMaterialId"],
                    "type": "audio",
                    "startMs": cumulative_offset_ms + drop_ms,
                    "durationMs": 1000,
                    "label": f"{case_id} · Drop {drop_index}",
                }
            )

        cumulative_offset_ms += source_material["durationMs"]

    timeline_id = f"timeline_{args.workspace_id}_{experience['styleId']}_{len(source_assets)}_{len(source_materials)}"
    editing_job_id = f"editing_job_{timeline_id}"

    export_package = {
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "sourceAssets": source_assets,
        "sourceMaterials": source_materials,
        "editingExperience": experience,
        "timelinePlan": {
            "timelineId": timeline_id,
            "workspaceId": args.workspace_id,
            "styleId": experience["styleId"],
            "sourceAssetIds": [asset["assetId"] for asset in source_assets],
            "sourceMaterialIds": [material["sourceMaterialId"] for material in source_materials],
            "targetDurationMs": cumulative_offset_ms,
            "tracks": [
                timeline_tracks["video"],
                timeline_tracks["subtitle"],
                timeline_tracks["overlay"],
                timeline_tracks["audio"],
            ],
        },
        "editingJob": {
            "jobId": editing_job_id,
            "timelineId": timeline_id,
            "renderer": "hyperframes",
            "status": "draft",
            "compositionPath": f"ai-service/output/plans/{timeline_id}.hyperframes/",
            "outputPath": f"ai-service/output/renders/{timeline_id}.final.mp4",
            "renderHints": {
                "fps": 30,
                "width": render_width,
                "height": render_height,
                "format": "mp4",
            },
        },
        "renderResult": {
            "renderId": f"render_{editing_job_id}",
            "jobId": editing_job_id,
            "status": "not_started",
            "outputPath": f"ai-service/output/renders/{timeline_id}.final.mp4",
            "previewAssetId": source_assets[0]["assetId"] if source_assets else None,
        },
    }

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(export_package, indent=2, ensure_ascii=False), encoding="utf-8")
    print(output_path)


def _load_editing_experience(template_path: Path) -> dict:
    template = json.loads(template_path.read_text(encoding="utf-8"))
    metadata = template.get("style_metadata", {})
    style_id = metadata.get("style_id", "mock-style")
    return {
        "experienceId": f"mock_{style_id}",
        "styleId": style_id,
        "category": metadata.get("category", "UNKNOWN"),
        "styleName": " ".join(part.capitalize() for part in style_id.split("-") if part),
        "pacingStyle": metadata.get("pacing_style", "UNKNOWN"),
        "visualTheme": metadata.get("visual_theme", "UNKNOWN"),
        "tags": metadata.get("tags", []),
        "sampleVideoDurationMs": metadata.get("sample_video_total_duration_ms", 0),
        "storylinePhases": [
            {
                "phaseId": phase.get("phase_id", "PHASE_UNKNOWN"),
                "narrativeGoal": phase.get("narrative_goal", ""),
                "startMs": phase.get("absolute_time_range", {}).get("start_ms", 0),
                "endMs": phase.get("absolute_time_range", {}).get("end_ms", 0),
                "durationMs": phase.get("absolute_time_range", {}).get("duration_ms", 0),
            }
            for phase in template.get("storyline_structure", [])
        ],
        "dynamicBeatCount": len(template.get("dynamic_pacing_blueprint", [])),
    }


def _load_source_material(
    case_dir: Path,
    case_id: str,
    max_video_clips_per_case: Optional[int] = None,
    smoke_duration_ms: Optional[int] = None,
) -> dict:
    audio = json.loads((case_dir / "step1_audio.json").read_text(encoding="utf-8"))
    transcript = json.loads((case_dir / "step2_transcript.json").read_text(encoding="utf-8"))
    visual = json.loads((case_dir / "step3_visual.json").read_text(encoding="utf-8"))
    style_hints = json.loads((case_dir / "elastic_template.json").read_text(encoding="utf-8"))
    visual_shots = [
        {
            "index": shot.get("index", 0),
            "startMs": shot.get("start_ms", 0),
            "endMs": shot.get("end_ms", 0),
            "shotType": shot.get("shot_type", "UNKNOWN"),
            "contentType": shot.get("content_type", "UNKNOWN"),
            "emotionalTone": shot.get("emotional_tone", "UNKNOWN"),
            "semanticPrompt": shot.get("b_roll_semantic_prompt", ""),
            "cameraMotionEffect": shot.get("camera_motion_effect", "UNKNOWN"),
            "editingUtility": shot.get("editing_utility", "UNKNOWN"),
        }
        for shot in visual.get("shots", [])
    ]
    if smoke_duration_ms is not None:
        visual_shots = [shot for shot in visual_shots if shot["startMs"] < smoke_duration_ms]
        if visual_shots:
            visual_shots = [
                {
                    **shot,
                    "endMs": min(shot["endMs"], smoke_duration_ms),
                }
                for shot in visual_shots
            ]
    if max_video_clips_per_case is not None:
        visual_shots = visual_shots[: max(0, max_video_clips_per_case)]

    transcript_sentences = [
        {
            "text": sentence.get("text", ""),
            "startMs": sentence.get("start_ms", 0),
            "endMs": sentence.get("end_ms", 0),
        }
        for sentence in transcript.get("sentences", [])
    ]
    if smoke_duration_ms is not None:
        transcript_sentences = [
            {
                **sentence,
                "endMs": min(sentence["endMs"], smoke_duration_ms),
            }
            for sentence in transcript_sentences
            if sentence["startMs"] < smoke_duration_ms
        ]

    beats_ms = audio.get("beats_ms", [])
    drops_ms = audio.get("drops_ms", [])
    if smoke_duration_ms is not None:
        beats_ms = [beat for beat in beats_ms if beat < smoke_duration_ms]
        drops_ms = [drop for drop in drops_ms if drop < smoke_duration_ms]

    duration_ms = audio.get("duration_ms", 0)
    if smoke_duration_ms is not None:
        duration_ms = min(duration_ms, smoke_duration_ms)

    return {
        "sourceMaterialId": f"source_material_{case_id}",
        "sourceCaseId": case_id,
        "durationMs": duration_ms,
        "bpm": audio.get("bpm", 0),
        "beatsMs": beats_ms,
        "dropsMs": drops_ms,
        "transcript": {
            "fullText": transcript.get("full_text", ""),
            "sentences": transcript_sentences,
        },
        "visualShots": visual_shots,
        "optionalStyleHints": {
            "styleId": style_hints.get("style_metadata", {}).get("style_id"),
            "storylinePhaseCount": len(style_hints.get("storyline_structure", [])),
            "narrativeGoals": [
                phase.get("narrative_goal", "")
                for phase in style_hints.get("storyline_structure", [])
                if phase.get("narrative_goal")
            ],
        },
    }


def _find_case_video(case_dir: Path) -> Path:
    candidates = sorted(
        file_path
        for file_path in case_dir.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in {".mp4", ".mov", ".webm", ".m4v"}
    )
    if not candidates:
        raise FileNotFoundError(f"No source video found in {case_dir}")
    return candidates[0]


def _probe_video(video_path: Path) -> tuple[int, int, float, int]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height:format=duration,size",
        "-of",
        "json",
        str(video_path),
    ]
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        return 1080, 1920, 0.0, 0

    payload = json.loads(process.stdout)
    stream = (payload.get("streams") or [{}])[0]
    format_info = payload.get("format", {})
    return (
        int(stream.get("width", 1080)),
        int(stream.get("height", 1920)),
        float(format_info.get("duration", 0.0)),
        int(float(format_info.get("size", 0))),
    )


if __name__ == "__main__":
    main()
