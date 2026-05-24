from pydantic import BaseModel


class MessageModel(BaseModel):
    role: str
    content: str
