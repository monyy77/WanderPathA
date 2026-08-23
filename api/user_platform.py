"""
WanderPathA User Platform API

This module exposes the HTTP API used by the User Platform frontend.

Flow:

Frontend (Bolt)
        |
POST /api/chat
        |
AgentRouter
        |
Planning / Memory / Flight / Refund / VIP
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.models import ChatRequest, ChatResponse
from api.agent_router import AgentRouter

app = FastAPI(
    title="WanderPathA User Platform API",
    version="1.0.0",
    description="Unified API for WanderPathA AI Agents",
)

# -------------------------------------------------------
# CORS
# -------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------
# Router
# -------------------------------------------------------

router = AgentRouter()

# -------------------------------------------------------
# Health Check
# -------------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": "WanderPathA User Platform API",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }

# -------------------------------------------------------
# Available Agents
# -------------------------------------------------------

@app.get("/api/agents")
async def list_agents():

    return [
        {
            "id": "memory",
            "name": "Memory Agent",
            "description": "Conversation memory and customer context",
        },
        {
            "id": "planning",
            "name": "Planning Agent",
            "description": "Task decomposition and planning",
        },
        {
            "id": "flight",
            "name": "Flight Agent",
            "description": "Flight rebooking workflows",
        },
        {
            "id": "refund",
            "name": "Refund Agent",
            "description": "Refund workflows",
        },
        {
            "id": "vip",
            "name": "VIP Agent",
            "description": "VIP trip customization",
        },
    ]

# -------------------------------------------------------
# Chat Endpoint
# -------------------------------------------------------

@app.post(
    "/api/chat",
    response_model=ChatResponse,
)
async def chat(request: ChatRequest):

    try:

        result = await router.route(
            agent_id=request.agent_id,
            message=request.message,
            session_id=request.session_id,
            customer_id=request.customer_id,
        )

        return ChatResponse(
            agent_id=request.agent_id,
            session_id=request.session_id,
            response=result.get("response", ""),
            execution=result.get(
                "execution",
                {
                    "status": "completed",
                },
            ),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(exc)}",
        )

# -------------------------------------------------------
# Local Development
# -------------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "api.user_platform:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
