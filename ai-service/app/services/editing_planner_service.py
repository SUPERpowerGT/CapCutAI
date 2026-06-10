from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import get_llm_settings
from app.providers import generate_llm_reply
from app.tools.build_ai4video_package import (
    _build_rule_based_timeline_plan,
    _load_editing_experience,
    _load_source_material,
)


@dataclass(frozen=True)
class EditingPlannerResult:
    timeline_plan_path: Path
    planner_info_path: Path
    provider: str
    model: str
    selected_video_clip_count: int
    target_duration_ms: int


def create_timeline_plan_with_llm(
    *,
    workspace_id: str,
    experience_path: Path,
    source_output_dirs: list[Path],
    source_video_names: list[str],
    output_path: Path,
    planner_info_path: Path,
    user_instruction: str = "",
) -> EditingPlannerResult:
    settings = get_llm_settings()
    if not settings.configured:
        raise RuntimeError(
            f"剪辑规划模型未配置：provider={settings.provider}, model={settings.model}"
        )

    experience = _load_editing_experience(experience_path)
    source_materials = [
        _load_source_material(material_dir=path, source_key=path.name)
        for path in source_output_dirs[:10]
    ]
    source_assets = [
        {
            "assetId": f"asset_source_{index}",
            "name": source_video_names[index - 1] if index - 1 < len(source_video_names) else f"source_{index}",
            "sourceMaterialId": material["sourceMaterialId"],
        }
        for index, material in enumerate(source_materials, start=1)
    ]

    planner_name = "llm_timeline_planner"
    fallback_reason = None
    resolved_model = settings.model

    try:
        prompt = _build_planner_prompt(
            workspace_id=workspace_id,
            user_instruction=user_instruction,
            experience=experience,
            source_assets=source_assets,
            source_materials=source_materials,
        )
        response_text, resolved_model = generate_llm_reply(settings, prompt)
        plan = _parse_json_object(response_text)
        if "timelinePlan" in plan:
            plan = plan["timelinePlan"]

        normalized_plan = _normalize_planner_output(
            raw_plan=plan,
            workspace_id=workspace_id,
            experience=experience,
            source_assets=source_assets,
            source_materials=source_materials,
        )
    except Exception as exception:
        planner_name = "rule_based_fallback"
        fallback_reason = _compact_exception_message(exception)
        normalized_plan = _build_rule_based_timeline_plan(
            timeline_id=f"timeline_{workspace_id}_{experience['styleId']}_fallback",
            workspace_id=workspace_id,
            experience=experience,
            source_assets=source_assets,
            source_materials=source_materials,
        )
    selected_video_clip_count = len(_clips_for_track(normalized_plan, "video"))
    if selected_video_clip_count == 0:
        raise RuntimeError("Gemini 剪辑规划没有返回可用视频片段。")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(normalized_plan, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    planner_info = {
        "planner": planner_name,
        "provider": settings.provider,
        "model": resolved_model,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sourceMaterialCount": len(source_materials),
        "selectedVideoClipCount": selected_video_clip_count,
        "targetDurationMs": normalized_plan["targetDurationMs"],
        "userInstruction": user_instruction,
    }
    if fallback_reason:
        planner_info["fallbackReason"] = fallback_reason
    planner_info_path.parent.mkdir(parents=True, exist_ok=True)
    planner_info_path.write_text(
        json.dumps(planner_info, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return EditingPlannerResult(
        timeline_plan_path=output_path,
        planner_info_path=planner_info_path,
        provider=f"{settings.provider}:{planner_name}" if fallback_reason else settings.provider,
        model=resolved_model,
        selected_video_clip_count=selected_video_clip_count,
        target_duration_ms=normalized_plan["targetDurationMs"],
    )


def _build_planner_prompt(
    *,
    workspace_id: str,
    user_instruction: str,
    experience: dict[str, Any],
    source_assets: list[dict[str, str]],
    source_materials: list[dict[str, Any]],
) -> str:
    planner_input = {
        "workspaceId": workspace_id,
        "userInstruction": user_instruction,
        "editingExperience": experience,
        "sourceAssets": source_assets,
        "sourceMaterials": [_compact_source_material(material) for material in source_materials],
    }
    return (
        "你是一个专业短视频剪辑 planner。请根据参考视频沉淀的 editingExperience，"
        "从用户上传的 sourceMaterials 中选择片段并生成可执行 timelinePlan。\n\n"
        "硬性要求：\n"
        "1. 只输出 JSON，不要 Markdown，不要解释文字。\n"
        "2. JSON 顶层必须是 timelinePlan 对象，字段包含 timelineId/workspaceId/styleId/sourceAssetIds/sourceMaterialIds/targetDurationMs/tracks。\n"
        "3. tracks 必须包含 video/subtitle/overlay/audio 四条 track。\n"
        "4. video clips 必须使用给定 assetId 和 sourceMaterialId，sourceStartMs 必须落在对应素材镜头范围内。\n"
        "5. 尽量模仿 editingExperience 的节奏、phase、情绪和开头 hook；不要简单顺序拼接全部素材。\n"
        "6. 输出视频 clip 请按成片时间连续排列，startMs 从 0 开始递增，单个片段 800ms 到 5000ms，目标总时长 12s 到 35s。\n"
        "7. subtitle clips 可以用 source transcript 中的句子，也可以基于画面生成极短中文字幕；字幕要和 video timeline 时间对齐。\n"
        "8. overlay/audio clips 作为节奏提示即可，可以为空数组，但 track 必须存在。\n\n"
        "输入数据如下：\n"
        f"{json.dumps(planner_input, ensure_ascii=False)}"
    )


def _compact_source_material(material: dict[str, Any]) -> dict[str, Any]:
    return {
        "sourceMaterialId": material["sourceMaterialId"],
        "sourceCaseId": material["sourceCaseId"],
        "durationMs": material["durationMs"],
        "bpm": material.get("bpm", 0),
        "dropsMs": material.get("dropsMs", [])[:20],
        "transcript": {
            "sentences": material.get("transcript", {}).get("sentences", [])[:40],
        },
        "visualShots": material.get("visualShots", [])[:80],
    }


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = (text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", stripped)
        if not match:
            raise
        return json.loads(match.group())


def _normalize_planner_output(
    *,
    raw_plan: dict[str, Any],
    workspace_id: str,
    experience: dict[str, Any],
    source_assets: list[dict[str, str]],
    source_materials: list[dict[str, Any]],
) -> dict[str, Any]:
    asset_ids = {asset["assetId"] for asset in source_assets}
    material_ids = {material["sourceMaterialId"] for material in source_materials}
    material_by_id = {material["sourceMaterialId"]: material for material in source_materials}
    tracks_by_type = {
        "video": {"trackId": "track_video_main", "type": "video", "clips": []},
        "subtitle": {"trackId": "track_caption_main", "type": "subtitle", "clips": []},
        "overlay": {"trackId": "track_overlay_main", "type": "overlay", "clips": []},
        "audio": {"trackId": "track_audio_main", "type": "audio", "clips": []},
    }

    for track in raw_plan.get("tracks", []):
        track_type = track.get("type")
        if track_type not in tracks_by_type:
            continue
        for raw_clip in track.get("clips", []):
            clip = _normalize_clip(
                raw_clip,
                track_type=track_type,
                asset_ids=asset_ids,
                material_ids=material_ids,
                material_by_id=material_by_id,
            )
            if clip:
                tracks_by_type[track_type]["clips"].append(clip)

    for track in tracks_by_type.values():
        track["clips"].sort(key=lambda clip: clip["startMs"])

    if not tracks_by_type["video"]["clips"]:
        raise RuntimeError("Planner output did not contain valid video clips.")

    target_duration_ms = max(
        clip["startMs"] + clip["durationMs"] for clip in tracks_by_type["video"]["clips"]
    )
    source_material_ids = [material["sourceMaterialId"] for material in source_materials]
    return {
        "timelineId": str(raw_plan.get("timelineId") or f"timeline_{workspace_id}_{experience['styleId']}_llm"),
        "workspaceId": workspace_id,
        "styleId": experience["styleId"],
        "sourceAssetIds": [asset["assetId"] for asset in source_assets],
        "sourceMaterialIds": source_material_ids,
        "targetDurationMs": max(1000, int(raw_plan.get("targetDurationMs") or target_duration_ms)),
        "tracks": [
            tracks_by_type["video"],
            tracks_by_type["subtitle"],
            tracks_by_type["overlay"],
            tracks_by_type["audio"],
        ],
    }


def _normalize_clip(
    raw_clip: dict[str, Any],
    *,
    track_type: str,
    asset_ids: set[str],
    material_ids: set[str],
    material_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    try:
        start_ms = max(0, int(raw_clip.get("startMs", 0)))
        duration_ms = max(100, int(raw_clip.get("durationMs", 0)))
    except (TypeError, ValueError):
        return None

    source_material_id = raw_clip.get("sourceMaterialId")
    if source_material_id is not None:
        source_material_id = str(source_material_id)
        if source_material_id not in material_ids:
            return None

    clip = {
        "clipId": str(raw_clip.get("clipId") or f"clip_{track_type}_{start_ms}"),
        "type": track_type,
        "startMs": start_ms,
        "durationMs": duration_ms,
        "label": str(raw_clip.get("label") or track_type),
    }
    if source_material_id:
        clip["sourceMaterialId"] = source_material_id

    if track_type == "video":
        asset_id = raw_clip.get("assetId")
        if asset_id is None or str(asset_id) not in asset_ids or not source_material_id:
            return None
        clip["assetId"] = str(asset_id)
        clip["sourceStartMs"] = _clamp_source_start_ms(
            raw_clip.get("sourceStartMs", 0),
            duration_ms=duration_ms,
            material=material_by_id[source_material_id],
        )
    elif raw_clip.get("sourceStartMs") is not None:
        try:
            clip["sourceStartMs"] = max(0, int(raw_clip["sourceStartMs"]))
        except (TypeError, ValueError):
            clip["sourceStartMs"] = 0

    if raw_clip.get("phaseId"):
        clip["phaseId"] = str(raw_clip["phaseId"])
    return clip


def _clamp_source_start_ms(raw_value: Any, *, duration_ms: int, material: dict[str, Any]) -> int:
    try:
        source_start_ms = max(0, int(raw_value))
    except (TypeError, ValueError):
        source_start_ms = 0
    material_duration_ms = max(0, int(material.get("durationMs", 0)))
    if material_duration_ms <= 0:
        return source_start_ms
    return min(source_start_ms, max(0, material_duration_ms - duration_ms))


def _clips_for_track(timeline_plan: dict[str, Any], track_type: str) -> list[dict[str, Any]]:
    for track in timeline_plan.get("tracks", []):
        if track.get("type") == track_type:
            return track.get("clips", [])
    return []


def _compact_exception_message(exception: Exception) -> str:
    message = str(exception).replace("\n", " ").strip()
    if "RESOURCE_EXHAUSTED" in message or "429" in message:
        return "Gemini quota/rate limit exhausted; used local rule-based planner fallback."
    if len(message) > 260:
        return f"{message[:257]}..."
    return message or exception.__class__.__name__
