from app.schemas.respond_request import AgentRespondRequest
from app.schemas.respond_response import AgentRespondResponse
from app.services.agent_service import build_agent_reply

from fastapi import APIRouter


router = APIRouter(prefix="/internal/agent", tags=["agent"])


@router.post("/respond", response_model=AgentRespondResponse)
def respond(request: AgentRespondRequest) -> AgentRespondResponse:
    return build_agent_reply(request)
