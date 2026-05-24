from pydantic import BaseModel, Field

from app.schemas.message import MessageModel


class AgentRespondRequest(BaseModel):
    conversation_id: str = Field(alias="conversationId")
    messages: list[MessageModel]
    context: dict | None = None

    model_config = {"populate_by_name": True}
