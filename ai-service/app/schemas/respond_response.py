from pydantic import BaseModel, Field


class ReplyModel(BaseModel):
    role: str
    content: str


class AgentRespondResponse(BaseModel):
    reply: ReplyModel
    status: str
    trace: list[str] = Field(default_factory=list)
    artifacts: dict = Field(default_factory=dict)
