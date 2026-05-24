from functools import lru_cache
from langgraph.graph import END, START, StateGraph

from app.config import get_llm_settings
from app.graph.state import AgentGraphState
from app.providers import generate_llm_reply


def _extract_latest_user_message(state: AgentGraphState) -> AgentGraphState:
    latest_user_message = next(
        (
            message["content"]
            for message in reversed(state.get("messages", []))
            if message.get("role", "").lower() == "user"
        ),
        "收到消息",
    )

    trace = [*state.get("trace", []), "graph.extract_latest_user_message"]

    return {
        **state,
        "latest_user_message": latest_user_message,
        "trace": trace,
    }


def _format_conversation(messages: list[dict[str, str]]) -> str:
    return "\n".join(
        f"{message.get('role', 'user').upper()}: {message.get('content', '').strip()}"
        for message in messages
        if message.get("content")
    )


def _build_unavailable_reply(
    state: AgentGraphState,
    reason: str,
    provider: str,
    model: str,
    error_message: str | None = None,
) -> AgentGraphState:
    trace = [*state.get("trace", []), reason]
    artifacts = {
        "timeline": None,
        "plugin": None,
        "llmProvider": provider,
        "model": model,
    }
    if error_message:
        artifacts["llmErrorMessage"] = error_message

    return {
        **state,
        "reply_content": f"{provider} 当前不可用，请检查本地配置或服务状态。",
        "status": "FAILED",
        "trace": trace,
        "artifacts": artifacts,
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

    conversation_text = _format_conversation(state.get("messages", []))
    prompt = (
        "You are CapCutAI's IM assistant.\n"
        "Answer the user's latest question helpfully and concisely.\n"
        "If the request is unclear, ask one concise clarifying question.\n\n"
        f"Conversation ID: {state.get('conversation_id', 'unknown')}\n"
        f"Conversation:\n{conversation_text}\n"
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

        trace = [*state.get("trace", []), f"graph.generate_reply.{settings.provider}"]
        return {
            **state,
            "reply_content": reply_text,
            "status": "COMPLETED",
            "trace": trace,
            "model_name": resolved_model_name,
            "artifacts": {
                "timeline": None,
                "plugin": None,
                "llmProvider": settings.provider,
                "model": resolved_model_name,
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
    graph.add_node("generate_reply", _generate_reply)
    graph.add_edge(START, "extract_latest_user_message")
    graph.add_edge("extract_latest_user_message", "generate_reply")
    graph.add_edge("generate_reply", END)
    return graph.compile()


def run_agent_graph(initial_state: AgentGraphState) -> AgentGraphState:
    compiled_graph = _build_graph()
    return compiled_graph.invoke(initial_state)
