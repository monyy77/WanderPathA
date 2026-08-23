from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class ChatRequest(BaseModel):
    agent: str
    message: str
    session_id: str
    customer_id: str


@app.post("/api/chat")
async def chat(request: ChatRequest):

    if request.agent == "planning":
        response = run_planning_agent(
            request.message
        )

    elif request.agent == "refund":
        response = run_refund_agent(
            request.message
        )

    elif request.agent == "flight":
        response = run_flight_agent(
            request.message
        )

    elif request.agent == "vip":
        response = run_vip_agent(
            request.message
        )

    elif request.agent == "memory":
        response = run_memory_agent(
            request.message
        )

    else:
        return {
            "error": "Unknown agent"
        }


    return {
        "agent": request.agent,
        "session_id": request.session_id,
        "response": response
    }
