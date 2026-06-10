from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from app.config import get_llm_settings
from app.graph.state import AgentGraphState
from app.memory import build_conversation_memory, build_workspace_memory
from app.prompts import build_conversation_prompt
from app.providers import generate_llm_reply
from app.services.reference_analysis_service import analyze_reference_video_from_workspace
from app.services.styled_video_service import _repo_root, create_styled_video_from_workspace
from app.tools import (
    describe_workspace_state,
    describe_workflow_tools,
    list_source_videos,
    validate_workspace_inputs,
)


def _trace(state: AgentGraphState, event: str) -> list[str]:
    return [*state.get("trace", []), event]


def _extract_latest_user_message(state: AgentGraphState) -> AgentGraphState:
    conversation_memory = build_conversation_memory(state.get("messages", []))
    return {
        **state,
        "latest_user_message": conversation_memory["latest_user_message"],
        "memory": {
            **state.get("memory", {}),
            "conversation": conversation_memory,
        },
        "trace": _trace(state, "graph.extract_latest_user_message"),
    }


def _hydrate_workspace_context(state: AgentGraphState) -> AgentGraphState:
    workspace_memory = build_workspace_memory(state.get("context"))

    return {
        **state,
        "meta": {
            "conversation_id": state.get("conversation_id"),
        },
        "workspace": workspace_memory["workspace"],
        "assets": workspace_memory["assets"],
        "memory": {
            **state.get("memory", {}),
            "workspace": workspace_memory,
        },
        "trace": _trace(state, "graph.hydrate_workspace_context"),
    }


def _classify_intent_name(user_message: str, assets: dict[str, object] | None = None) -> str:
    normalized = user_message.lower()
    assets = assets or {}

    if any(
        keyword in normalized
        for keyword in [
            "进度",
            "跑完",
            "完成了吗",
            "完成没",
            "产物",
            "结果在哪",
            "输出在哪",
            "有没有生成",
            "查一下",
            "检索",
            "分析好了",
            "分析好",
            "elastic_template",
        ]
    ):
        return "WORKFLOW_STATUS"

    wants_analysis = any(
        keyword in normalized
        for keyword in ["分析", "拆解", "reference", "爆款", "风格分析", "解析一下", "帮我分析"]
    )
    wants_edit = any(
        keyword in normalized
        for keyword in [
            "生成",
            "剪",
            "制作",
            "制片",
            "做视频",
            "做成",
            "做一版",
            "风格化",
            "styled",
            "create",
            "edit this video",
            "demo",
            "样片",
            "一版",
            "拼一个",
            "拼个",
            "出一版",
        ]
    )

    if wants_analysis and wants_edit:
        return "ANALYZE_AND_CREATE_STYLED_VIDEO"

    if wants_analysis and assets.get("has_reference_video") and assets.get("has_source_video"):
        return "ANALYZE_AND_CREATE_STYLED_VIDEO"

    if wants_analysis:
        return "ANALYZE_REFERENCE"

    if wants_edit and assets.get("has_reference_video") and assets.get("has_source_video") and not any(
        keyword in normalized for keyword in ["经验", "刚刚分析", "已分析", "之前", "历史", "已有"]
    ):
        return "ANALYZE_AND_CREATE_STYLED_VIDEO"

    if wants_edit:
        return "CREATE_STYLED_VIDEO"

    if assets.get("has_reference_video") and assets.get("has_source_video") and any(
        keyword in normalized for keyword in ["开始", "处理", "搞一下", "走一下", "帮我弄", "继续"]
    ):
        return "ANALYZE_AND_CREATE_STYLED_VIDEO"

    if any(keyword in normalized for keyword in ["修改", "调整", "revision", "revise"]):
        return "REVISE_VIDEO"

    return "CHAT"


def _classify_intent(state: AgentGraphState) -> AgentGraphState:
    latest_user_message = state.get("latest_user_message", "收到消息")
    pending_workflow = _pending_workflow_from_messages(state.get("messages", []))
    if pending_workflow and _is_confirmation_message(latest_user_message):
        intent_name = pending_workflow
        is_confirmed = True
    else:
        intent_name = _classify_intent_name(latest_user_message, state.get("assets", {}))
        is_confirmed = False

    return {
        **state,
        "intent": {
            "name": intent_name,
            "user_instruction": latest_user_message,
            "requires_reference": intent_name in {"ANALYZE_REFERENCE", "ANALYZE_AND_CREATE_STYLED_VIDEO"},
            "requires_source": intent_name in {"CREATE_STYLED_VIDEO", "ANALYZE_AND_CREATE_STYLED_VIDEO", "REVISE_VIDEO"},
            "confirmed": is_confirmed,
            "pending_workflow": pending_workflow,
        },
        "status": "UNDERSTANDING",
        "trace": _trace(state, f"graph.classify_intent.{intent_name.lower()}"),
    }


def _is_confirmation_message(message: str) -> bool:
    normalized = message.strip().lower()
    confirmation_keywords = [
        "确认",
        "开始",
        "执行",
        "制作",
        "剪辑",
        "去吧",
        "可以",
        "可以的",
        "对的",
        "ok",
        "okay",
        "yes",
        "go",
    ]
    cancel_keywords = ["取消", "不要", "先别", "等等", "暂停", "stop", "cancel"]
    return any(keyword in normalized for keyword in confirmation_keywords) and not any(
        keyword in normalized for keyword in cancel_keywords
    )


def _pending_workflow_from_messages(messages: list[dict[str, str]]) -> str | None:
    for message in reversed(messages[:-1]):
        role = message.get("role", "").strip().upper()
        if role != "ASSISTANT":
            continue
        content = message.get("content", "")
        if "确认开始分析并剪辑" in content or "确认开始分析并制作" in content:
            return "ANALYZE_AND_CREATE_STYLED_VIDEO"
        if (
            "确认开始剪辑" in content
            or "确认开始制作" in content
            or "待确认工作流：CREATE_STYLED_VIDEO" in content
        ):
            return "CREATE_STYLED_VIDEO"
        if "确认开始分析" in content or "待确认工作流：ANALYZE_REFERENCE" in content:
            return "ANALYZE_REFERENCE"
        return None
    return None


def _collect_tool_context(state: AgentGraphState) -> AgentGraphState:
    workspace = state.get("workspace", {})
    assets = state.get("assets", {})
    intent = state.get("intent", {})
    intent_name = intent.get("name", "CHAT")
    latest_user_message = str(state.get("latest_user_message", ""))
    previous_analysis = _inspect_latest_workflow_outputs(workspace)

    if (
        intent_name == "ANALYZE_AND_CREATE_STYLED_VIDEO"
        and previous_analysis.get("found")
        and assets.get("has_source_video")
        and not any(keyword in latest_user_message for keyword in ["重新分析", "重跑分析", "重新解析", "再分析一次"])
    ):
        intent_name = "CREATE_STYLED_VIDEO"
        intent = {
            **intent,
            "name": intent_name,
            "requires_reference": False,
            "requires_source": True,
            "using_previous_reference_analysis": True,
        }

    tool_calls = [
        describe_workspace_state(workspace, assets),
        describe_workflow_tools(intent_name, assets),
        list_source_videos(assets),
        validate_workspace_inputs(intent_name, assets),
    ]
    tool_calls.append({"tool": "inspect_latest_reference_analysis", **previous_analysis})

    validation_result = next(
        (call for call in tool_calls if call.get("tool") == "validate_workspace_inputs"),
        {"missing_inputs": [], "is_ready": True},
    )
    if (
        intent_name == "CREATE_STYLED_VIDEO"
        and "reference_video" in validation_result.get("missing_inputs", [])
        and previous_analysis.get("found")
    ):
        missing_inputs = [
            item for item in validation_result.get("missing_inputs", []) if item != "reference_video"
        ]
        validation_result = {
            **validation_result,
            "missing_inputs": missing_inputs,
            "is_ready": len(missing_inputs) == 0,
            "using_previous_reference_analysis": True,
        }
        tool_calls = [
            validation_result if call.get("tool") == "validate_workspace_inputs" else call
            for call in tool_calls
        ]

    return {
        **state,
        "intent": intent,
        "tool_calls": tool_calls,
        "status": "PLANNING" if validation_result.get("is_ready") else "MISSING_INPUT",
        "trace": _trace(state, "graph.collect_tool_context"),
    }


def _should_execute_workflow(state: AgentGraphState) -> str:
    if state.get("status") == "MISSING_INPUT":
        return "reply_missing_input"

    intent_name = state.get("intent", {}).get("name", "CHAT")
    if intent_name not in {"ANALYZE_REFERENCE", "CREATE_STYLED_VIDEO", "ANALYZE_AND_CREATE_STYLED_VIDEO"}:
        if intent_name == "WORKFLOW_STATUS":
            return "reply_workflow_status"
        return "generate_reply"

    validation = next(
        (call for call in state.get("tool_calls", []) if call.get("tool") == "validate_workspace_inputs"),
        {"is_ready": False},
    )
    if not validation.get("is_ready"):
        return "generate_reply"

    if not state.get("intent", {}).get("confirmed"):
        return "reply_workflow_confirmation"

    if intent_name == "ANALYZE_REFERENCE":
        return "execute_reference_analysis_workflow"

    if intent_name == "CREATE_STYLED_VIDEO":
        return "execute_styled_video_workflow"

    if intent_name == "ANALYZE_AND_CREATE_STYLED_VIDEO":
        return "execute_analyze_and_create_workflow"

    return "generate_reply"


def _reply_workflow_confirmation(state: AgentGraphState) -> AgentGraphState:
    intent_name = state.get("intent", {}).get("name", "CHAT")
    assets = state.get("assets", {})

    if intent_name == "ANALYZE_REFERENCE":
        reference_video = assets.get("reference_video") or {}
        reply_lines = [
            "我可以开始分析这条参考/爆款视频。",
            f"参考视频：{reference_video.get('name') or '已上传视频'}",
            "这一步会调用 AI4Video，生成音频、转写、视觉分析和 elastic_template.json。",
            "确认后我再执行，避免误跑长任务。",
            "",
            "确认请回复：确认开始分析",
        ]
        workflow = "ANALYZE_REFERENCE"
    elif intent_name == "CREATE_STYLED_VIDEO":
        source_count = min(int(assets.get("source_video_count") or 0), 10)
        previous_analysis = next(
            (call for call in state.get("tool_calls", []) if call.get("tool") == "inspect_latest_reference_analysis"),
            {},
        )
        previous_line = (
            f"将使用之前的参考分析：{previous_analysis.get('styleId') or 'unknown'}"
            if previous_analysis.get("found")
            else "将使用当前参考视频或已分析的参考经验。"
        )
        reply_lines = [
            "我可以根据已分析的参考经验，开始剪辑当前 source 素材。",
            f"将使用 source 视频数量：{source_count} 个（最多 10 个）",
            previous_line,
            "这一步会分析 source 素材、生成 timeline_plan，并渲染 demo 成片。",
            "确认后我再执行，避免误跑模型和渲染任务。",
            "",
            "确认请回复：确认开始制作",
        ]
        workflow = "CREATE_STYLED_VIDEO"
    elif intent_name == "ANALYZE_AND_CREATE_STYLED_VIDEO":
        reference_video = assets.get("reference_video") or {}
        source_count = min(int(assets.get("source_video_count") or 0), 10)
        reply_lines = [
            "我看到当前同时有爆款/参考视频和 source 素材。",
            "更合理的顺序是：先分析参考视频沉淀经验，然后直接用这份经验剪辑 source 素材。",
            f"参考视频：{reference_video.get('name') or '已上传视频'}",
            f"source 视频数量：{source_count} 个（最多 10 个）",
            "确认后我会连续执行：AI4Video 分析 -> 剪辑规划 -> 本地渲染 demo。",
            "",
            "确认请回复：确认开始分析并剪辑",
        ]
        workflow = "ANALYZE_AND_CREATE_STYLED_VIDEO"
    else:
        reply_lines = ["我可以执行这个工作流。确认后我再开始。", "确认请回复：确认开始"]
        workflow = intent_name

    reply = "\n".join(reply_lines)
    return {
        **state,
        "reply_content": reply,
        "status": "WAITING_CONFIRMATION",
        "trace": _trace(state, "graph.reply_workflow_confirmation"),
        "artifacts": {
            "timeline": None,
            "plugin": None,
            "workflow": workflow,
            "requiresConfirmation": True,
            "toolCalls": state.get("tool_calls", []),
        },
        "response": {
            "assistant_text": reply,
        },
    }


def _reply_workflow_status(state: AgentGraphState) -> AgentGraphState:
    status_result = _inspect_latest_workflow_outputs(state.get("workspace", {}))

    if status_result.get("found"):
        reply_lines = [
            "我查了当前 workspace 的固定产物，参考视频分析已经完成。",
            f"风格经验：{status_result.get('styleId') or 'unknown'}",
            "现在可以直接用这份经验剪 source 素材；如果要重跑分析，再明确说“重新分析”。",
        ]
    else:
        reply_lines = [
            "我查了当前 workspace 的固定产物，还没有找到完成的参考视频分析。",
            "缺少 assets/template/elastic_template.json；需要先分析参考视频，或者确认是不是切到了别的 workspace。",
        ]

    reply = "\n".join(reply_lines)
    return {
        **state,
        "reply_content": reply,
        "status": "COMPLETED" if status_result.get("found") else "MISSING_INPUT",
        "trace": _trace(state, "graph.reply_workflow_status"),
        "artifacts": {
            "timeline": None,
            "plugin": None,
            "workflow": "WORKFLOW_STATUS",
            "toolCalls": state.get("tool_calls", []),
            **status_result,
        },
        "response": {
            "assistant_text": reply,
        },
    }


def _summarize_exception(exception: Exception) -> str:
    raw_message = str(exception)
    normalized = raw_message.lower()
    if "resource_exhausted" in normalized or "429" in normalized or "quota" in normalized:
        return "模型额度或限流已触发，请稍后重试，或切换到可用的模型/API key。"
    if "invalid api key" in normalized or "401" in normalized or "无效的api key" in normalized:
        return "API key 无效或没有权限，请检查对应模型的 token 配置。"
    if "ffprobe" in normalized and "no such file or directory" in normalized:
        return "视频探测工具 ffprobe 不可用，请检查 ffmpeg/ffprobe 环境配置。"
    if "ffmpeg" in normalized and "no such file or directory" in normalized:
        return "视频渲染工具 ffmpeg 不可用，请检查 ffmpeg 环境配置。"
    if "video file not found" in normalized or "reference video not found" in normalized or "not found" in normalized:
        return "找不到需要处理的视频文件，请确认素材仍在当前 workspace 目录里。"
    if "missing experience template" in normalized or "elastic_template" in normalized:
        return "缺少参考视频分析产物 elastic_template.json，请先完成参考视频分析。"
    if "timed out" in normalized or "timeout" in normalized:
        return "外部模型或本地处理超时，请稍后重试。"
    compact = " ".join(raw_message.split())
    if len(compact) > 180:
        return f"{compact[:177]}..."
    return compact or exception.__class__.__name__


def _inspect_latest_workflow_outputs(workspace: dict[str, object]) -> dict[str, object]:
    workspace_id = str(workspace.get("workspace_id") or "workspace_unknown")
    workspace_folder = workspace.get("workspace_folder_path")
    if isinstance(workspace_folder, str) and workspace_folder:
        workspace_root = Path(workspace_folder).expanduser()
        fixed_template = workspace_root / "assets" / "template" / "elastic_template.json"
        if fixed_template.exists():
            return _workflow_output_status_from_template(
                template_path=fixed_template,
                intermediate_dir=workspace_root / "assets" / "intermediate",
                workspace_id=workspace_id,
                source="workspace_fixed_artifact",
            )

    roots = [
        _repo_root() / "ai-service" / "output" / "im-runs" / _slug_for_path(workspace_id),
    ]
    if isinstance(workspace_folder, str) and workspace_folder:
        roots.append(Path(workspace_folder).expanduser())

    candidates: list[Path] = []
    for root in roots:
        if root.exists():
            candidates.extend(root.rglob("elastic_template.json"))

    if not candidates:
        return {
            "found": False,
            "workspaceId": workspace_id,
            "checkedRoots": [str(root) for root in roots],
        }

    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    intermediate_dir = latest.parent
    if latest.parent.name == "template" and latest.parent.parent.name == "assets":
        intermediate_dir = latest.parent.parent / "intermediate"
    return _workflow_output_status_from_template(
        template_path=latest,
        intermediate_dir=intermediate_dir,
        workspace_id=workspace_id,
        source="latest_discovered_artifact",
    )


def _workflow_output_status_from_template(
    *,
    template_path: Path,
    intermediate_dir: Path,
    workspace_id: str,
    source: str,
) -> dict[str, object]:
    style_id = None
    category = None
    try:
        elastic_template = json.loads(template_path.read_text(encoding="utf-8"))
        style_metadata = elastic_template.get("style_metadata", {})
        style_id = style_metadata.get("style_id")
        category = style_metadata.get("category")
    except (OSError, json.JSONDecodeError, TypeError):
        pass

    return {
        "found": True,
        "workspaceId": workspace_id,
        "source": source,
        "outputDir": str(intermediate_dir),
        "elasticTemplatePath": str(template_path),
        "step1AudioPath": str(intermediate_dir / "step1_audio.json")
        if (intermediate_dir / "step1_audio.json").exists()
        else None,
        "step2TranscriptPath": str(intermediate_dir / "step2_transcript.json")
        if (intermediate_dir / "step2_transcript.json").exists()
        else None,
        "step3VisualPath": str(intermediate_dir / "step3_visual.json")
        if (intermediate_dir / "step3_visual.json").exists()
        else None,
        "styleId": style_id,
        "category": category,
    }


def _slug_for_path(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value).strip("_") or "workspace"


def _reply_missing_input(state: AgentGraphState) -> AgentGraphState:
    intent_name = state.get("intent", {}).get("name", "CHAT")
    validation = next(
        (call for call in state.get("tool_calls", []) if call.get("tool") == "validate_workspace_inputs"),
        {"missing_inputs": []},
    )
    missing_inputs = validation.get("missing_inputs", [])

    if intent_name == "ANALYZE_REFERENCE" and "reference_video" in missing_inputs:
        reply = (
            "还缺参考视频。先在左侧素材区上传一条爆款/参考视频到当前 workspace，"
            "上传后直接在这里说“帮我分析一下这个爆款视频”，我就会开始跑分析链路。"
        )
    elif intent_name == "CREATE_STYLED_VIDEO":
        previous_analysis = next(
            (call for call in state.get("tool_calls", []) if call.get("tool") == "inspect_latest_reference_analysis"),
            {},
        )
        if "reference_video" in missing_inputs and "source_video" in missing_inputs:
            reply = (
                "还缺两类素材：参考视频和待剪素材。先上传一条参考视频，再上传至少一条 source video，"
                "然后直接说“按这个风格帮我拼一个 demo”或“按这个风格帮我剪一版”。"
            )
        elif "reference_video" in missing_inputs:
            if previous_analysis.get("found"):
                reply = (
                    "当前没有新的参考视频，但我找到了之前沉淀的爆款分析数据。\n"
                    f"历史风格：{previous_analysis.get('styleId') or 'unknown'}\n"
                    "如果要用这份历史经验剪当前 source 素材，请回复：确认开始制作\n"
                    "如果要换一个爆款风格，请先上传新的参考视频。"
                )
            else:
                reply = (
                    "当前只有 source 素材，还没有可用的爆款/参考视频经验。\n"
                    "请先上传一条爆款/参考视频，或者先分析一条参考视频后，我才能按它的风格剪这些素材。"
                )
        else:
            reply = (
                "还缺待剪素材。先上传至少一条 source video，上传后我就可以按参考风格开始拼 demo。"
            )
    elif intent_name == "ANALYZE_AND_CREATE_STYLED_VIDEO":
        if "reference_video" in missing_inputs and "source_video" in missing_inputs:
            reply = "还缺参考视频和 source 素材。请先上传一条爆款/参考视频，以及至少一条待剪 source 视频。"
        elif "reference_video" in missing_inputs:
            reply = "还缺爆款/参考视频。请先上传参考视频，我会先分析它，再用经验剪 source 素材。"
        else:
            reply = "还缺 source 素材。参考视频可以先分析，但要生成 demo 还需要至少一条待剪 source 视频。"
    else:
        reply = "当前缺少执行这条请求所需的输入素材，请先补齐后再试。"

    return {
        **state,
        "reply_content": reply,
        "status": "MISSING_INPUT",
        "trace": _trace(state, "graph.reply_missing_input"),
        "artifacts": {
            "timeline": None,
            "plugin": None,
            "toolCalls": state.get("tool_calls", []),
            "intent": state.get("intent", {}),
            "missingInputs": missing_inputs,
        },
        "response": {
            "assistant_text": reply,
        },
    }


def _execute_reference_analysis_workflow(state: AgentGraphState) -> AgentGraphState:
    try:
        result = analyze_reference_video_from_workspace(
            state.get("workspace", {}),
            state.get("assets", {}),
            conversation_id=state.get("conversation_id", "conversation_unknown"),
        )
    except Exception as exception:
        summary = _summarize_exception(exception)
        return {
            **state,
            "reply_content": f"参考视频分析没有成功：{summary}",
            "status": "FAILED",
            "trace": _trace(state, f"graph.execute_reference_analysis_workflow.failed.{exception.__class__.__name__}"),
            "artifacts": {
                "timeline": None,
                "plugin": None,
                "toolCalls": state.get("tool_calls", []),
                "workflow": "ANALYZE_REFERENCE",
                "error": summary,
                "errorType": exception.__class__.__name__,
            },
            "error": {
                "code": "reference_analysis_failed",
                "message": summary,
                "recoverable": True,
            },
        }

    reply_lines = [
        "参考视频分析完成。",
        f"已沉淀风格经验：{result.get('styleId') or 'unknown'}",
    ]

    return {
        **state,
        "reply_content": "\n".join(reply_lines),
        "status": "COMPLETED",
        "trace": _trace(state, "graph.execute_reference_analysis_workflow.completed"),
        "artifacts": {
            "timeline": None,
            "plugin": None,
            "toolCalls": state.get("tool_calls", []),
            **result,
        },
        "response": {
            "assistant_text": "\n".join(reply_lines),
        },
    }


def _execute_styled_video_workflow(state: AgentGraphState) -> AgentGraphState:
    try:
        result = create_styled_video_from_workspace(
            state.get("workspace", {}),
            state.get("assets", {}),
            conversation_id=state.get("conversation_id", "conversation_unknown"),
            user_instruction=state.get("latest_user_message", ""),
        )
    except Exception as exception:
        summary = _summarize_exception(exception)
        return {
            **state,
            "reply_content": f"剪辑没有成功：{summary}",
            "status": "FAILED",
            "trace": _trace(state, f"graph.execute_styled_video_workflow.failed.{exception.__class__.__name__}"),
            "artifacts": {
                "timeline": None,
                "plugin": None,
                "toolCalls": state.get("tool_calls", []),
                "workflow": "CREATE_STYLED_VIDEO",
                "error": summary,
                "errorType": exception.__class__.__name__,
            },
            "error": {
                "code": "styled_video_workflow_failed",
                "message": summary,
                "recoverable": True,
            },
        }

    reply_lines = [
        "已经按参考视频经验完成剪辑，并产出了一版 demo 成片。",
    ]
    if result.get("plannerModel"):
        reply_lines.append(
            f"剪辑规划模型：{result.get('plannerProvider')} / {result.get('plannerModel')}"
        )
    if result.get("selectedVideoClipCount"):
        reply_lines.append(f"已选择片段数：{result['selectedVideoClipCount']}")
    if result.get("externalAudioPath"):
        reply_lines.append(f"已覆盖参考音频：{result['externalAudioPath']}")

    return {
        **state,
        "reply_content": "\n".join(reply_lines),
        "status": "COMPLETED",
        "trace": _trace(state, "graph.execute_styled_video_workflow.completed"),
        "artifacts": {
            "timeline": result["packagePath"],
            "plugin": None,
            "toolCalls": state.get("tool_calls", []),
            **result,
        },
        "response": {
            "assistant_text": "\n".join(reply_lines),
        },
    }


def _execute_analyze_and_create_workflow(state: AgentGraphState) -> AgentGraphState:
    try:
        analysis_result = analyze_reference_video_from_workspace(
            state.get("workspace", {}),
            state.get("assets", {}),
            conversation_id=state.get("conversation_id", "conversation_unknown"),
        )
        styled_result = create_styled_video_from_workspace(
            state.get("workspace", {}),
            state.get("assets", {}),
            conversation_id=state.get("conversation_id", "conversation_unknown"),
            user_instruction=state.get("latest_user_message", ""),
        )
    except Exception as exception:
        summary = _summarize_exception(exception)
        return {
            **state,
            "reply_content": f"分析并剪辑没有成功：{summary}",
            "status": "FAILED",
            "trace": _trace(state, f"graph.execute_analyze_and_create_workflow.failed.{exception.__class__.__name__}"),
            "artifacts": {
                "timeline": None,
                "plugin": None,
                "toolCalls": state.get("tool_calls", []),
                "workflow": "ANALYZE_AND_CREATE_STYLED_VIDEO",
                "error": summary,
                "errorType": exception.__class__.__name__,
            },
            "error": {
                "code": "analyze_and_create_workflow_failed",
                "message": summary,
                "recoverable": True,
            },
        }

    reply_lines = [
        "参考视频已经分析完成，并已用这份经验剪出一版 demo 成片。",
        f"风格经验：{analysis_result.get('styleId') or 'unknown'}",
    ]
    if styled_result.get("plannerModel"):
        reply_lines.append(
            f"剪辑规划模型：{styled_result.get('plannerProvider')} / {styled_result.get('plannerModel')}"
        )

    artifacts = {
        **analysis_result,
        **styled_result,
        "workflow": "CREATE_STYLED_VIDEO",
        "analysisWorkflow": "ANALYZE_REFERENCE",
        "timeline": styled_result["packagePath"],
        "plugin": None,
        "toolCalls": state.get("tool_calls", []),
    }

    return {
        **state,
        "reply_content": "\n".join(reply_lines),
        "status": "COMPLETED",
        "trace": _trace(state, "graph.execute_analyze_and_create_workflow.completed"),
        "artifacts": artifacts,
        "response": {
            "assistant_text": "\n".join(reply_lines),
        },
    }


def _build_unavailable_reply(
    state: AgentGraphState,
    reason: str,
    provider: str,
    model: str,
    error_message: str | None = None,
) -> AgentGraphState:
    trace = _trace(state, reason)
    artifacts = {
        "timeline": None,
        "plugin": None,
        "llmProvider": provider,
        "model": model,
        "toolCalls": state.get("tool_calls", []),
    }
    if error_message:
        artifacts["llmErrorMessage"] = error_message

    return {
        **state,
        "reply_content": f"{provider} 当前不可用，请检查本地配置或服务状态。",
        "status": "FAILED",
        "trace": trace,
        "artifacts": artifacts,
        "error": {
            "code": "provider_unavailable",
            "message": error_message or reason,
            "recoverable": True,
        },
    }


def _generate_reply(state: AgentGraphState) -> AgentGraphState:
    settings = get_llm_settings()

    if not settings.configured:
        return _build_unavailable_reply(
            state,
            f"graph.provider_not_configured.{settings.provider}",
            settings.provider,
            settings.model,
        )

    conversation_memory = state.get("memory", {}).get("conversation", {})
    prompt = build_conversation_prompt(
        conversation_id=state.get("conversation_id", "unknown"),
        latest_user_message=state.get("latest_user_message", "收到消息"),
        conversation_transcript=conversation_memory.get("transcript", ""),
        workspace=state.get("workspace", {}),
        assets=state.get("assets", {}),
        intent=state.get("intent", {}),
        tool_calls=state.get("tool_calls", []),
    )

    try:
        reply_text, resolved_model_name = generate_llm_reply(settings, prompt)
        if not reply_text:
            return _build_unavailable_reply(
                state,
                f"graph.empty_response.{settings.provider}",
                settings.provider,
                settings.model,
            )

        trace = _trace(state, f"graph.generate_reply.{settings.provider}")
        return {
            **state,
            "reply_content": reply_text,
            "response": {
                "assistant_text": reply_text,
            },
            "status": "COMPLETED",
            "trace": trace,
            "model_name": resolved_model_name,
            "artifacts": {
                "timeline": None,
                "plugin": None,
                "llmProvider": settings.provider,
                "model": resolved_model_name,
                "toolCalls": state.get("tool_calls", []),
                "intent": state.get("intent", {}),
            },
        }
    except Exception as exception:
        fallback_state = _build_unavailable_reply(
            state,
            f"graph.provider_error.{settings.provider}.{exception.__class__.__name__}",
            settings.provider,
            settings.model,
            str(exception),
        )
        fallback_artifacts = dict(fallback_state.get("artifacts", {}))
        fallback_artifacts["llmError"] = exception.__class__.__name__
        fallback_state["artifacts"] = fallback_artifacts
        return fallback_state


@lru_cache(maxsize=1)
def _build_graph():
    graph = StateGraph(AgentGraphState)
    graph.add_node("extract_latest_user_message", _extract_latest_user_message)
    graph.add_node("hydrate_workspace_context", _hydrate_workspace_context)
    graph.add_node("classify_intent", _classify_intent)
    graph.add_node("collect_tool_context", _collect_tool_context)
    graph.add_node("reply_missing_input", _reply_missing_input)
    graph.add_node("reply_workflow_confirmation", _reply_workflow_confirmation)
    graph.add_node("reply_workflow_status", _reply_workflow_status)
    graph.add_node("execute_reference_analysis_workflow", _execute_reference_analysis_workflow)
    graph.add_node("execute_styled_video_workflow", _execute_styled_video_workflow)
    graph.add_node("execute_analyze_and_create_workflow", _execute_analyze_and_create_workflow)
    graph.add_node("generate_reply", _generate_reply)
    graph.add_edge(START, "extract_latest_user_message")
    graph.add_edge("extract_latest_user_message", "hydrate_workspace_context")
    graph.add_edge("hydrate_workspace_context", "classify_intent")
    graph.add_edge("classify_intent", "collect_tool_context")
    graph.add_conditional_edges(
        "collect_tool_context",
        _should_execute_workflow,
        {
            "reply_missing_input": "reply_missing_input",
            "reply_workflow_confirmation": "reply_workflow_confirmation",
            "reply_workflow_status": "reply_workflow_status",
            "execute_reference_analysis_workflow": "execute_reference_analysis_workflow",
            "execute_styled_video_workflow": "execute_styled_video_workflow",
            "execute_analyze_and_create_workflow": "execute_analyze_and_create_workflow",
            "generate_reply": "generate_reply",
        },
    )
    graph.add_edge("reply_missing_input", END)
    graph.add_edge("reply_workflow_confirmation", END)
    graph.add_edge("reply_workflow_status", END)
    graph.add_edge("execute_reference_analysis_workflow", END)
    graph.add_edge("execute_styled_video_workflow", END)
    graph.add_edge("execute_analyze_and_create_workflow", END)
    graph.add_edge("generate_reply", END)
    return graph.compile()


def run_agent_graph(initial_state: AgentGraphState) -> AgentGraphState:
    compiled_graph = _build_graph()
    return compiled_graph.invoke(initial_state)
