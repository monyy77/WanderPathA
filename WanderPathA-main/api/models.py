from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    """
    User request model.
    AgentRouter classifies the message and picks the agent automatically.
    """
    message: str
    session_id: Optional[str] = None
    customer_id: Optional[str] = None
    agent_id: Optional[str] = None  # kept for backward compatibility


class ChatResponse(BaseModel):
    """
    Unified response returned to frontend — matches the Bolt chat UI's
    expected shape (session_id, agent_id, message_id, role, content,
    status, steps, created_at).
    """
    agent_id: str
    session_id: Optional[str] = None
    message_id: str
    role: str = "assistant"
    content: str
    status: str
    steps: List[dict] = []
    created_at: str
