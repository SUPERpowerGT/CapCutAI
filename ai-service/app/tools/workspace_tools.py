from __future__ import annotations

from typing import Any


def describe_workspace_state(
    workspace: dict[str, Any], assets: dict[str, Any]
) -> dict[str, Any]:
    summary_parts = []

    workspace_title = workspace.get("workspace_title") or "Unknown workspace"
    summary_parts.append(f"Workspace: {workspace_title}")

    if assets.get("reference_video"):
        summary_parts.append("Reference video is available.")
    else:
        summary_parts.append("Reference video is missing.")

    source_video_count = assets.get("source_video_count", 0)
    if source_video_count > 0:
        summary_parts.append(f"{source_video_count} source video(s) available.")
    else:
        summary_parts.append("No source videos available.")

    if workspace.get("source_directory_path"):
        summary_parts.append(
            f"Source directory: {workspace.get('source_directory_path')}"
        )

    return {
        "tool": "describe_workspace_state",
        "summary": " ".join(summary_parts),
        "workspace": workspace,
        "assets": {
            "has_reference_video": assets.get("has_reference_video", False),
            "has_source_video": assets.get("has_source_video", False),
            "source_video_count": source_video_count,
        },
    }


def list_source_videos(assets: dict[str, Any]) -> dict[str, Any]:
    source_videos = assets.get("source_videos", [])
    items = [
        {
            "asset_id": asset.get("asset_id"),
            "name": asset.get("name"),
            "workspace_relative_path": asset.get("workspace_relative_path"),
            "mime_type": asset.get("mime_type"),
        }
        for asset in source_videos
    ]

    return {
        "tool": "list_source_videos",
        "count": len(items),
        "items": items,
    }


def describe_workflow_tools(
    intent_name: str, assets: dict[str, Any]
) -> dict[str, Any]:
    tools: list[dict[str, Any]] = []

    if assets.get("has_reference_video"):
        tools.append(
            {
                "name": "analyze_reference_video",
                "intent": "ANALYZE_REFERENCE",
                "ready": True,
                "description": "Run AI4Video on the uploaded reference video and produce elastic_template.json plus intermediate analysis JSON files.",
            }
        )

    if assets.get("has_reference_video") and assets.get("has_source_video"):
        tools.append(
            {
                "name": "analyze_then_create_styled_video",
                "intent": "ANALYZE_AND_CREATE_STYLED_VIDEO",
                "ready": True,
                "description": "Analyze the uploaded reference video first, then use that fresh editing experience to plan and render a styled draft from up to 10 source videos.",
            }
        )
        tools.append(
            {
                "name": "create_styled_video",
                "intent": "CREATE_STYLED_VIDEO",
                "ready": True,
                "description": "Analyze up to 10 source videos, use the configured LLM to plan an edit from the reference style experience, build an editing package, and render a draft MP4.",
            }
        )

    return {
        "tool": "describe_workflow_tools",
        "intent": intent_name,
        "items": tools,
    }


def validate_workspace_inputs(
    intent_name: str, assets: dict[str, Any]
) -> dict[str, Any]:
    missing_inputs: list[str] = []

    if intent_name == "ANALYZE_REFERENCE" and not assets.get("has_reference_video"):
        missing_inputs.append("reference_video")

    if intent_name == "ANALYZE_AND_CREATE_STYLED_VIDEO":
        if not assets.get("has_reference_video"):
            missing_inputs.append("reference_video")
        if not assets.get("has_source_video"):
            missing_inputs.append("source_video")

    if intent_name in {"CREATE_STYLED_VIDEO", "REVISE_VIDEO"} and not assets.get(
        "has_source_video"
    ):
        missing_inputs.append("source_video")

    if intent_name == "CREATE_STYLED_VIDEO" and not assets.get("has_reference_video"):
        missing_inputs.append("reference_video")

    return {
        "tool": "validate_workspace_inputs",
        "intent": intent_name,
        "missing_inputs": missing_inputs,
        "is_ready": len(missing_inputs) == 0,
    }
