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
LLM Router
        |
MCP Registry
        |
MCP Client
        |
WanderPath MCP Server
        |
Selected Capability / Tool Execution
"""


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


from api.models import (
    ChatRequest,
    ChatResponse,
)


from api.agent_router import AgentRouter


from api.mcp_client import MCPClient


from api.mcp_registry import MCPRegistry


from api.llm_factory import get_llm





# =======================================================
# FastAPI Application
# =======================================================


app = FastAPI(

    title="WanderPathA User Platform API",

    version="1.0.0",

    description=
    "Unified API for WanderPathA AI Agents",

)






# =======================================================
# CORS
# =======================================================


app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)






# =======================================================
# MCP + LLM Initialization
# =======================================================


"""
Runtime dependencies:


LLM

 |
 +--> Gemini / Groq



MCP Client

 |
 +--> FastMCP Client

 |
 +--> WanderPath MCP Server



MCP Registry

 |
 +--> Runtime discovered MCP tools

"""



# MCP Server connection

mcp_client = MCPClient(

    server_url="http://localhost:8080"

)



# Runtime MCP capabilities registry

mcp_registry = MCPRegistry(

    mcp_client

)



# LLM Provider

llm = get_llm()






# =======================================================
# Agent Router
# =======================================================


router = AgentRouter(

    llm=llm,

    mcp_registry=mcp_registry,

)








# =======================================================
# Health Check
# =======================================================


@app.get("/")
async def root():


    return {


        "service":

            "WanderPathA User Platform API",


        "status":

            "running",

    }






@app.get("/health")
async def health():


    return {


        "status":

            "healthy",

    }








# =======================================================
# Available Agents
# =======================================================


@app.get("/api/agents")
async def list_agents():


    return [


        {

            "id":

                "memory",


            "name":

                "Memory Agent",


            "description":

                "Conversation memory and customer context",

        },


        {

            "id":

                "planning",


            "name":

                "Planning Agent",


            "description":

                "Task decomposition and planning",

        },


        {

            "id":

                "flight",


            "name":

                "Flight Agent",


            "description":

                "Flight rebooking workflows",

        },


        {

            "id":

                "refund",


            "name":

                "Refund Agent",


            "description":

                "Refund workflows",

        },


        {

            "id":

                "vip",


            "name":

                "VIP Agent",


            "description":

                "VIP trip customization",

        },

    ]










# =======================================================
# Chat Endpoint
# =======================================================


@app.post(

    "/api/chat",

    response_model=ChatResponse,

)

async def chat(request: ChatRequest):


    try:


        # User sends only message.
        #
        # Router decides:
        #
        # Planning
        # Memory
        # Flight
        # Refund
        # VIP
        #
        # using:
        #
        # LLM + MCP Runtime Discovery


        result = router.route(

            {


                "message":

                    request.message,


                "session_id":

                    request.session_id,


                "customer_id":

                    request.customer_id,


            }

        )






        return ChatResponse(


            agent_id=

                result.get(

                    "agent",

                    "unknown",

                ),



            session_id=

                request.session_id,



            response=

                result.get(

                    "result",

                    "",

                ),



            execution={


                "status":

                    result.get(

                        "status",

                        "completed",

                    ),



                "agent":

                    result.get(

                        "agent",

                        "unknown",

                    ),

            },


        )






    except ValueError as exc:


        raise HTTPException(

            status_code=400,

            detail=str(exc),

        )






    except Exception as exc:


        raise HTTPException(

            status_code=500,

            detail=

                f"Internal server error: {str(exc)}",

        )










# =======================================================
# Local Development
# =======================================================


if __name__ == "__main__":


    import uvicorn



    uvicorn.run(

        "api.user_platform:app",

        host="0.0.0.0",

        port=8000,

        reload=True,

    )
