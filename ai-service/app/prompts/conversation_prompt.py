from __future__ import annotations

from typing import Any


def _format_tool_calls(tool_calls: list[dict[str, Any]]) -> str:
    if not tool_calls:
        return "No tool calls were executed."

    lines = []
    for call in tool_calls:
        tool = call.get("tool", "unknown_tool")
        result = {key: value for key, value in call.items() if key != "tool"}
        lines.append(f"- {tool}: {result}")
    return "\n".join(lines)


def build_conversation_prompt(
    *,
    conversation_id: str,
    latest_user_message: str,
    conversation_transcript: str,
    workspace: dict[str, Any],
    assets: dict[str, Any],
    intent: dict[str, Any],
    tool_calls: list[dict[str, Any]],
) -> str:
    workspace_title = workspace.get("workspace_title") or "Unknown workspace"
    workspace_folder_path = workspace.get("workspace_folder_path") or "Unknown path"
    reference_dir = workspace.get("reference_directory_path") or "Unknown path"
    source_dir = workspace.get("source_directory_path") or "Unknown path"
    source_count = assets.get("source_video_count", 0)

    return (
        "You are CapCutAI's agent inside a desktop video editing workspace.\n"
        "Be concise, practical, and context-aware.\n"
        "Do not pretend a video is ready if required assets are missing.\n"
        "If required inputs are missing, clearly tell the user what to upload or prepare next.\n"
        "If the request is unclear, ask one short clarifying question.\n\n"
        f"Conversation ID: {conversation_id}\n"
        f"Latest user message: {latest_user_message}\n\n"
        "Workspace Memory:\n"
        f"- Title: {workspace_title}\n"
        f"- Folder: {workspace_folder_path}\n"
        f"- Reference directory: {reference_dir}\n"
        f"- Source directory: {source_dir}\n"
        f"- Reference uploaded: {'yes' if assets.get('has_reference_video') else 'no'}\n"
        f"- Source videos uploaded: {'yes' if assets.get('has_source_video') else 'no'}\n"
        f"- Source video count: {source_count}\n\n"
        "Intent:\n"
        f"- Name: {intent.get('name', 'UNKNOWN')}\n"
        f"- Needs reference: {'yes' if intent.get('requires_reference') else 'no'}\n"
        f"- Needs source: {'yes' if intent.get('requires_source') else 'no'}\n\n"
        "Tool Results:\n"
        f"{_format_tool_calls(tool_calls)}\n\n"
        "Conversation Transcript:\n"
        f"{conversation_transcript or 'No previous conversation.'}\n"
    )
