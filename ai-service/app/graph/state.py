from typing import Any, TypedDict


class AgentGraphState(TypedDict, total=False):
    conversation_id: str
    messages: list[dict[str, str]]
    context: dict[str, Any]
    meta: dict[str, Any]
    workspace: dict[str, Any]
    assets: dict[str, Any]
    memory: dict[str, Any]
    intent: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    response: dict[str, Any]
    latest_user_message: str
    reply_content: str
    trace: list[str]
    artifacts: dict[str, Any]
    status: str
    model_name: str
    error: dict[str, Any]
