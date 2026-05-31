from __future__ import annotations

from typing import Any


def _coerce_video_asset(asset: dict[str, Any] | None) -> dict[str, Any] | None:
    if not asset:
        return None

    return {
        "asset_id": asset.get("assetId"),
        "name": asset.get("name"),
        "mime_type": asset.get("mimeType"),
        "duration_seconds": asset.get("durationSeconds"),
        "frame_width": asset.get("frameWidth"),
        "frame_height": asset.get("frameHeight"),
        "workspace_file_path": asset.get("workspaceFilePath"),
        "workspace_relative_path": asset.get("workspaceRelativePath"),
    }


def build_workspace_memory(context: dict[str, Any] | None) -> dict[str, Any]:
    context = context or {}
    source_videos = [
        asset
        for asset in (
            _coerce_video_asset(item) for item in context.get("sourceVideos", [])
        )
        if asset
    ]
    reference_video = _coerce_video_asset(context.get("referenceVideo"))
    selected_source_video = _coerce_video_asset(context.get("sourceVideo"))

    workspace = {
        "workspace_id": context.get("workspaceId"),
        "workspace_title": context.get("workspaceTitle"),
        "workspace_folder_path": context.get("workspaceFolderPath"),
        "reference_directory_path": context.get("referenceDirectoryPath"),
        "source_directory_path": context.get("sourceDirectoryPath"),
    }
    assets = {
        "has_reference_video": bool(context.get("hasReferenceVideo")),
        "has_source_video": bool(context.get("hasSourceVideo")),
        "reference_video": reference_video,
        "selected_source_video": selected_source_video,
        "source_videos": source_videos,
        "source_video_count": len(source_videos),
    }

    return {
        "workspace": workspace,
        "assets": assets,
    }


def build_conversation_memory(messages: list[dict[str, str]]) -> dict[str, Any]:
    transcript_lines = []
    latest_user_message = "收到消息"

    for message in messages:
        role = message.get("role", "user").strip().lower() or "user"
        content = message.get("content", "").strip()
        if not content:
            continue

        transcript_lines.append(f"{role.upper()}: {content}")
        if role == "user":
            latest_user_message = content

    return {
        "latest_user_message": latest_user_message,
        "transcript": "\n".join(transcript_lines),
        "message_count": len(transcript_lines),
    }
