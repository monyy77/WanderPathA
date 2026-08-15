"""
Planning Agent entry point: IROPS reshuffle
("a flight has been disrupted -- replan every affected booking").

This is a NEW agent, sitting next to the existing Memory/RAG agent
(agent/agent.py). It reuses the same MCP server (server/server.py) and the
same database (db/), and does not touch or duplicate the memory/RAG code
path -- it only imports `discover_tools`, a two-line helper with no memory
logic in it, to avoid re-implementing MCP tool discovery.

Supports two modes against the same real request type, per the lab's DAG
concern:
    - "decomposition_first": planning/decomposition.py
    - "dynamic":              planning/dynamic_decomposition.py

Both are thin adaptations of the reference toolkit
(AmrSheta22/task_decomposition_and_planning), wired to real MCP tools and
the real `travel_agency` DB instead of the toolkit's generic text-only demo.

Trace format follows the toolkit's cli.py `save_artifact` convention (JSON
per run under artifacts/), extended with call-count/latency so the same
traces back the comparison table in planning_eval/ (Person 3's concern) --
no second logging system.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from agent.agent import discover_tools  # reused, not duplicated -- see module docstring
from ..rag.planning import planner_router
from .dag import Plan
from .Decomposition import decompose_goal, execute_plan, final_output
from .Dynamic_decomposition import dynamic_decomposition

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts"

PlanningMode = Literal["decomposition_first", "dynamic"]


def build_llm():
    """Same provider/model the existing WanderPathA agent already uses
    (agent/agent.py:build_structured_model) -- swapped in for the toolkit's
    default ChatMistralAI, per the lab's 'swap the model provider, keep the
    interfaces' instruction."""
    return init_chat_model(
        model="llama-3.3-70b-versatile",
        model_provider="groq",
        max_tokens=1024,
        max_retries=3,
    )


def save_artifact(payload: dict) -> Path:
    ARTIFACT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = ARTIFACT_DIR / f"planning-run-{stamp}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


async def run_planning_agent(
    client: Any,
    goal: str,
    mode: PlanningMode = "decomposition_first",
) -> dict:
    """Run the IROPS Planning Agent once and return the trace payload.

    `client` is the same MultiServerMCPClient session pattern used by the
    existing agent (see client/client.py) -- this agent reuses the live MCP
    connection, it does not stand up a second server.
    """
    tools = await discover_tools(client)
    llm = build_llm()
    planner_router.configure(llm)

    started = time.perf_counter()
    payload: dict = {
        "agent": "planning_agent (IROPS reshuffle)",
        "mode": mode,
        "goal": goal,
        "model": "llama-3.3-70b-versatile",
    }

    if mode == "decomposition_first":
        plan: Plan = decompose_goal(goal, llm, tool_names=list(tools.keys()))
        outputs = await execute_plan(
            plan, llm, mcp_tools=tools, planner_router=planner_router.route_task
        )
        result = final_output(plan, outputs)
        payload.update(
            plan=plan.model_dump(),
            execution_batches=plan.execution_batches(),
            outputs=outputs,
            result=result,
            llm_calls=len(plan.tasks),  # 1 planning call + 1 per non-tool node, refined by eval harness
        )
    elif mode == "dynamic":
        history = await dynamic_decomposition(goal, llm, mcp_tools=tools)
        result = history[-1][2] if history else "Planner reported the goal was already complete."
        payload.update(
            history=[{"kind": k, "task": t, "result": r} for k, t, r in history],
            result=result,
            llm_calls=len(history) * 2,  # one decision call + one execution call per step
        )
    else:
        raise ValueError(f"Unknown planning mode: {mode!r}")

    payload["latency_seconds"] = round(time.perf_counter() - started, 3)
    artifact_path = save_artifact(payload)
    payload["artifact_path"] = str(artifact_path)
    return payload


async def main() -> None:
    """Manual smoke test. Run with: python -m planning.planning_agent
    (from an active MCP client session, mirroring main.py's pattern)."""
    from client.client import create_client

    client = await create_client()
    try:
        goal = (
            "Flight 2 (CAI to JED) has been delayed 120 minutes due to bad "
            "weather, with a high connection-risk flag. Reshuffle every "
            "booking affected by this disruption: assess priority, find "
            "rebooking or transport alternatives, and propose a plan per "
            "customer including any compensation owed."
        )
        result = await run_planning_agent(client, goal, mode="decomposition_first")
        print("\n=== PLANNING AGENT RESULT (decomposition-first) ===")
        print(result["result"])
        print(f"\nArtifact saved: {result['artifact_path']}")
    finally:
        if hasattr(client, "close"):
            await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
