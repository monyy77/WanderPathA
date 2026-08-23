from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    agent_id: str
    message: str
    session_id: str
    customer_id: Optional[str] = None


class ChatResponse(BaseModel):
    agent_id: str
    session_id: str
    response: str
    execution: dict
