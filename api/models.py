from pydantic import BaseModel
from typing import Optional, Any


class ChatRequest(BaseModel):
    """
    User request model.

    The user no longer selects the agent.
    AgentRouter will classify the message
    and choose the correct agent automatically.
    """

    message: str

    session_id: Optional[str] = None

    customer_id: Optional[str] = None

    # Optional for backward compatibility
    # Not required from frontend anymore.
    agent_id: Optional[str] = None



class ChatResponse(BaseModel):
    """
    Unified response returned to frontend.
    """

    agent_id: str

    session_id: Optional[str] = None

    response: str

    execution: dict[str, Any]
