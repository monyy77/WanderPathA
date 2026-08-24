"""
api/user_platform.py

WanderPathA User Platform API
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.models import ChatRequest, ChatResponse
from api.mcp_client import MCPClient
from api.mcp_registry import MCPRegistry
from api.agent_router import LLMRouter
from api.llm_factory import get_llm

logger = logging.getLogger(__name__)

# ==========================================================
# FastAPI
# ==========================================================

app = FastAPI(

    title="WanderPathA User Platform API",

    version="1.0.0",

    description="Unified API for WanderPathA",

)

# ==========================================================
# CORS
# ==========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)

# ==========================================================
# Runtime Objects
# ==========================================================

mcp_client = MCPClient(
    "http://127.0.0.1:9000"
)

mcp_registry = MCPRegistry(
    mcp_client
)

llm = get_llm()

router = LLMRouter(
    llm,
    mcp_registry,
)

# ==========================================================
# In-memory Sessions
# ==========================================================

sessions = {}

# ==========================================================
# Startup / Shutdown
# ==========================================================

@app.on_event("startup")
async def startup():

    logger.info("Connecting to MCP Server...")

    await mcp_client.connect()

    await mcp_registry.refresh()

@app.on_event("shutdown")
async def shutdown():

    logger.info("Disconnecting MCP...")

    await mcp_client.disconnect()

# ==========================================================
# Root
# ==========================================================

@app.get("/")
async def root():

    return {

        "service": "WanderPathA",

        "status": "running",

    }

# ==========================================================
# Health
# ==========================================================

@app.get("/health")
async def health():

    try:

        tools = await mcp_registry.list_tool_names()

        return {

            "status": "healthy",

            "mcp": True,

            "tools": len(tools),

        }

    except Exception:

        return {

            "status": "degraded",

            "mcp": False,

        }

# ==========================================================
# Runtime Tools
# ==========================================================

@app.get("/api/tools")
async def list_tools():

    return await mcp_registry.list_capabilities()

@app.post("/api/reload")
async def reload_registry():

    await mcp_registry.refresh()

    return {

        "status": "reloaded"

    }

# ==========================================================
# Agents
# ==========================================================

@app.get("/api/agents")
async def agents():

    return [

        {

            "id": "dynamic",

            "name": "Dynamic MCP Router",

            "description": "Runtime capability routing"

        }

    ]

# ==========================================================
# Chat
# ==========================================================

@app.post(

    "/api/chat",

    response_model=ChatResponse,

)

async def chat(

    request: ChatRequest,

):

    try:

        session_id = request.session_id

        if not session_id:

            session_id = str(

                uuid.uuid4()

            )

        if session_id not in sessions:

            sessions[session_id] = []

        sessions[session_id].append(

            {

                "role": "user",

                "content": request.message,

            }

        )

        decision = await router.classify(

            request.message

        )

        if decision.capability is None:

            raise HTTPException(

                status_code=400,

                detail="No suitable MCP capability."

            )

        result = await mcp_client.call_tool(

            decision.capability,

            {

                "message": request.message,

                "customer_id": request.customer_id,

            }

        )

        sessions[session_id].append(

            {

                "role": "assistant",

                "content": str(result),

            }

        )

        return ChatResponse(

            agent_id=decision.capability,

            session_id=session_id,

            message_id=str(uuid.uuid4()),

            role="assistant",

            content=str(result),

            status="completed",

            steps=[],

            created_at=datetime.utcnow().isoformat(),

        )

    except HTTPException:

        raise

    except Exception as exc:

        logger.exception(

            "Chat failed"

        )

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )

# ==========================================================
# Local Development
# ==========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "api.user_platform:app",

        host="0.0.0.0",

        port=8000,

        reload=True,

    )