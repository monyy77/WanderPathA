"""
Planning Agent entry point: IROPS reshuffle
("a flight has been disrupted -- replan every affected booking").

This agent is responsible for selecting and executing
advanced planners:

- Plan and Solve
- Tree of Thoughts
- LATS

It reuses the existing MCP Server and database tools.
"""


from __future__ import annotations


import json
import time

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_core.callbacks import BaseCallbackHandler



from planning.environment import TravelEnvironment
from planning.planner_selector import PlannerSelector


from planning.tool_registry import MCPToolRegistry

from planning.schema import PlannerType, PlannerResult

from planning.dag import Plan

from planning.decomposition import (
    decompose_goal,
    execute_plan,
    final_output,
)
from planning.dynamic_decomposition import dynamic_decomposition



load_dotenv()



ROOT = Path(__file__).resolve().parents[1]

ARTIFACT_DIR = ROOT / "artifacts"



PlanningMode = Literal[
    "decomposition_first",
    "dynamic"
]



async def discover_tools(
    client
) -> dict:

    """
    Discover available MCP tools.
    """

    tools_list = await client.get_tools()


    return {
        tool.name: tool
        for tool in tools_list
    }




class TokenTracker(BaseCallbackHandler):


    def __init__(self):

        self.llm_calls = 0

        self.input_tokens = 0

        self.output_tokens = 0

        self.total_tokens = 0

        self.peak_input_tokens = 0



    def on_llm_end(
        self,
        response,
        **kwargs
    ):

        self.llm_calls += 1


        try:

            usage = response.llm_output.get(
                "token_usage",
                {}
            )


            input_tokens = usage.get(
                "prompt_tokens",
                0
            )


            output_tokens = usage.get(
                "completion_tokens",
                0
            )


            total_tokens = usage.get(
                "total_tokens",
                0
            )


            self.input_tokens += input_tokens

            self.output_tokens += output_tokens

            self.total_tokens += total_tokens


            self.peak_input_tokens = max(

                self.peak_input_tokens,

                input_tokens

            )


        except Exception:

            pass



    def as_dict(self):

        return {

            "llm_calls":
                self.llm_calls,


            "input_tokens":
                self.input_tokens,


            "output_tokens":
                self.output_tokens,


            "total_tokens":
                self.total_tokens,


            "peak_input_tokens":
                self.peak_input_tokens

        }




def build_llm():
    return init_chat_model(
        model="mistral-large-latest",
        temperature=0,
        max_retries=10, 
    timeout=120,
    )
    

def create_execution_plan(
    planner_result: PlannerResult,
) -> list[dict]:
    """
    Convert planner output into an execution plan.
    """

    return [
        {
            "task": planner_result.task_id,
            "tool": planner_result.metadata.get(
                "selected_node",
                planner_result.planner.value,
            ),
            "input": planner_result.output,
        }
    ]


def save_artifact(
    payload: dict
) -> Path:


    ARTIFACT_DIR.mkdir(
        exist_ok=True
    )


    stamp = datetime.now(

        timezone.utc

    ).strftime(

        "%Y%m%dT%H%M%SZ"

    )



    path = (

        ARTIFACT_DIR

        /

        f"planning-run-{stamp}.json"

    )



    path.write_text(

        json.dumps(

            payload,

            indent=2,

            ensure_ascii=False,

            default=str

        ),

        encoding="utf-8"

    )


    return path





async def run_planning_agent(

    client: Any,

    goal: str,

    mode: PlanningMode = "decomposition_first",

) -> dict:



    tools = await discover_tools(
        client
    )
    tool_registry = MCPToolRegistry(
        tools
    )

    environment = TravelEnvironment(
        mcp_client=client
    )




    llm = build_llm()



    tracker = TokenTracker()



    llm = llm.with_config(

        {

            "callbacks":

            [

                tracker

            ]

        }

    )
    planner_selector = PlannerSelector(
        llm,
        tool_registry,
        environment,
    )



    started = time.perf_counter()



    payload = {

        "agent":

        "planning_agent (IROPS reshuffle)",


        "mode":

        mode,


        "goal":

        goal,


        "model":

        "mistral-large-latest"
             

    }




    if mode == "decomposition_first":


        plan: Plan = decompose_goal(
        
                    goal,
        
                    llm,
        
                    tool_names=list(
                        tools.keys()
                    )
        
                )


        async def planner_executor(
            task,
            outputs,
            goal,
        ):

            result = await planner_selector.execute_planned_task(
                task,
                outputs,
                goal,
            )

            result.execution_plan = create_execution_plan(
                result
            )

            return result



        outputs = await execute_plan(

            plan,

            llm,

            mcp_tools=tools,

            planner_executor=planner_executor,

        )



        result = final_output(

            plan,

            outputs

        )



        payload.update(

            {

                "plan":

                    plan.model_dump(),


                "execution_batches":

                    plan.execution_batches(),


                "outputs":

                    outputs,


                "result":

                    result

            }

        )





    elif mode == "dynamic":



        history = await dynamic_decomposition(

            goal,

            llm,

            mcp_tools=tools

        )



        result = (

            history[-1][2]

            if history

            else

            "Planner reported the goal was already complete."

        )



        payload.update(

            {

                "history":

                [

                    {

                        "kind":

                        kind,


                        "task":

                        task,


                        "result":

                        result

                    }

                    for kind, task, result in history

                ],


                "result":

                result

            }

        )



    else:


        raise ValueError(

            f"Unknown planning mode: {mode}"

        )




    payload["token_usage"] = tracker.as_dict()



    payload["latency_seconds"] = round(

        time.perf_counter() - started,

        3

    )



    artifact_path = save_artifact(

        payload

    )


    payload["artifact_path"] = str(

        artifact_path

    )



    return payload


async def main() -> None:
    """
    Manual smoke test.

    Run with:
        python -m planning.planning_agent
    """

    from client.client import create_client

    client = await create_client()

    try:
        goal = (
            "Flight 2 (CAI to JED) has been delayed 120 "
            "minutes due to bad weather, with a high "
            "connection-risk flag. Reshuffle every booking "
            "affected by this disruption: assess priority, "
            "find rebooking or transport alternatives, and "
            "propose a plan per customer including any "
            "compensation owed."
        )

        result = await run_planning_agent(
            client,
            goal,
            mode="decomposition_first",
        )

        print(
            "\n=== PLANNING AGENT RESULT "
            "(decomposition-first) ==="
        )

        print(
            result["result"]
        )

        print(
            f"\nArtifact saved: "
            f"{result['artifact_path']}"
        )

    finally:
        if hasattr(client, "close"):
            await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())


'''
Planning Agent
      │
      ▼
Discover MCP Tools
      │
      ▼
Create Tool Registry
      │
      ▼
Create Environment
      │
      ▼
Create PlannerSelector (مرة واحدة)
      │
      ▼
Decomposition
      │
      ▼
execute_plan()
      │
      ▼
planner_executor()
      │
      ▼
PlannerSelector.execute_planned_task()
      │
 ┌────┴──────────────┐
 │       │           │
 ▼       ▼           ▼
P&S     ToT        LATS
 │       │           │
 └───────┴───────────┘
         │
         ▼
 MCP Tool Registry
         │
         ▼
    MCP Server
         │
         ▼
     Database
'''
