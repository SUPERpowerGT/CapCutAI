from typing import Any, TypedDict


class AgentGraphState(TypedDict, total=False):
    conversation_id: str
    messages: list[dict[str, str]]
    latest_user_message: str
    reply_content: str
    trace: list[str]
    artifacts: dict[str, Any]
    status: str
    model_name: str
