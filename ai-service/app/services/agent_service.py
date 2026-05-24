from app.config import get_llm_settings
from app.graph import run_agent_graph
from app.schemas.respond_request import AgentRespondRequest
from app.schemas.respond_response import AgentRespondResponse, ReplyModel


def build_agent_reply(request: AgentRespondRequest) -> AgentRespondResponse:
    settings = get_llm_settings()
    final_state = run_agent_graph(
        {
            "conversation_id": request.conversation_id,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in request.messages
            ],
            "trace": ["received conversation payload", "selected langgraph agent flow"],
        }
    )

    return AgentRespondResponse(
        reply=ReplyModel(
            role="assistant",
            content=final_state.get("reply_content", "Mock agent 已收到：收到消息"),
        ),
        status=final_state.get("status", "COMPLETED"),
        trace=[*final_state.get("trace", []), "returned assistant reply"],
        artifacts=final_state.get(
            "artifacts",
            {
                "timeline": None,
                "plugin": None,
                "llmProvider": settings.provider,
                "model": settings.model,
            },
        ),
    )
