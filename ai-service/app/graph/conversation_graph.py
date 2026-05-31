from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.config import get_llm_settings
from app.graph.state import AgentGraphState
from app.memory import build_conversation_memory, build_workspace_memory
from app.prompts import build_conversation_prompt
from app.providers import generate_llm_reply
from app.tools import (
    describe_workspace_state,
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


def _classify_intent_name(user_message: str) -> str:
    normalized = user_message.lower()

    if any(keyword in normalized for keyword in ["分析", "拆解", "reference", "爆款", "风格分析"]):
        return "ANALYZE_REFERENCE"

    if any(
        keyword in normalized
        for keyword in ["生成", "剪", "做成", "风格化", "styled", "create", "edit this video"]
    ):
        return "CREATE_STYLED_VIDEO"

    if any(keyword in normalized for keyword in ["修改", "调整", "revision", "revise"]):
        return "REVISE_VIDEO"

    return "CHAT"


def _classify_intent(state: AgentGraphState) -> AgentGraphState:
    latest_user_message = state.get("latest_user_message", "收到消息")
    intent_name = _classify_intent_name(latest_user_message)

    return {
        **state,
        "intent": {
            "name": intent_name,
            "user_instruction": latest_user_message,
            "requires_reference": intent_name in {"ANALYZE_REFERENCE", "CREATE_STYLED_VIDEO"},
            "requires_source": intent_name in {"CREATE_STYLED_VIDEO", "REVISE_VIDEO"},
        },
        "status": "UNDERSTANDING",
        "trace": _trace(state, f"graph.classify_intent.{intent_name.lower()}"),
    }


def _collect_tool_context(state: AgentGraphState) -> AgentGraphState:
    workspace = state.get("workspace", {})
    assets = state.get("assets", {})
    intent = state.get("intent", {})
    intent_name = intent.get("name", "CHAT")

    tool_calls = [
        describe_workspace_state(workspace, assets),
        list_source_videos(assets),
        validate_workspace_inputs(intent_name, assets),
    ]

    validation_result = next(
        (call for call in tool_calls if call.get("tool") == "validate_workspace_inputs"),
        {"missing_inputs": [], "is_ready": True},
    )

    return {
        **state,
        "tool_calls": tool_calls,
        "status": "PLANNING" if validation_result.get("is_ready") else "MISSING_INPUT",
        "trace": _trace(state, "graph.collect_tool_context"),
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
    graph.add_node("generate_reply", _generate_reply)
    graph.add_edge(START, "extract_latest_user_message")
    graph.add_edge("extract_latest_user_message", "hydrate_workspace_context")
    graph.add_edge("hydrate_workspace_context", "classify_intent")
    graph.add_edge("classify_intent", "collect_tool_context")
    graph.add_edge("collect_tool_context", "generate_reply")
    graph.add_edge("generate_reply", END)
    return graph.compile()


def run_agent_graph(initial_state: AgentGraphState) -> AgentGraphState:
    compiled_graph = _build_graph()
    return compiled_graph.invoke(initial_state)
