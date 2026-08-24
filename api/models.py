from pydantic import BaseModel
from typing import Optional, Any, List


class ChatRequest(BaseModel):

    message: str

    session_id: Optional[str] = None

    customer_id: Optional[str] = None

    agent_id: Optional[str] = None



class ChatResponse(BaseModel):

    agent_id: str

    session_id: Optional[str] = None

    message_id: str

    role: str = "assistant"

    content: str

    status: str

    steps: List[dict] = []

    created_at: str
