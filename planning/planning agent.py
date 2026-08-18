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



from .environment import TravelEnvironment
from .planner_selector import PlannerSelector

from .plan_and_solve import PlanAndSolvePlanner
from .tree_of_thoughts import TreeOfThoughtsPlanner
from .lats import LATSPlanner

from .tool_registry import MCPToolRegistry

from .schema import PlannerType, PlannerResult

from .dag import Plan

from .decomposition import (
    decompose_goal,
    execute_plan,
    final_output,
)

from .dynamic_decomposition import dynamic_decomposition



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

        model="llama-3.3-70b-versatile",

        model_provider="groq",

        max_tokens=1024,

        max_retries=3,

    )




async def execute_planned_task(

    task,

    outputs,

    goal,

    llm,

    client,

) -> PlannerResult:


    """
    Select planner and execute subtask.

    Person 1 only calls this function.
    """



    selector = PlannerSelector(
        llm
    )


    planner_type = selector.select_planner(
        task.instruction
    )



    tool_registry = MCPToolRegistry(
        client
    )



    if planner_type == PlannerType.PLAN_AND_SOLVE:


        planner = PlanAndSolvePlanner(

            llm,

            tool_registry

        )



    elif planner_type == PlannerType.TREE_OF_THOUGHTS:


        planner = TreeOfThoughtsPlanner(

            llm,

            tool_registry

        )



    elif planner_type == PlannerType.LATS:



        environment = TravelEnvironment(

            database=None

        )


        planner = LATSPlanner(

            llm,

            tool_registry,

            environment

        )


    else:


        raise ValueError(

            f"Unsupported planner {planner_type}"

        )


    result = await planner.run(

        task_id=task.id,

        task=task.instruction

    )


    return result


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



    started = time.perf_counter()



    payload = {

        "agent":

        "planning_agent (IROPS reshuffle)",


        "mode":

        mode,


        "goal":

        goal,


        "model":

        "llama-3.3-70b-versatile"

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
            goal
        ):

            return await execute_planned_task(

                task,

                outputs,

                goal,

                llm,

                client,

            )



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
User Goal
    |
Planning Agent
    |
Decomposition
    |
Subtask
    |
Planner Selector
    |
 -----------------------
 |          |           |
P&S        ToT         LATS
 |          |           |
Async Planner.run()
 |
await MCP Tool
 |
MCP Server
 |
Database
'''

 
'''
run_planning_agent()
        |
await execute_plan()
        |
await planner_executor()
        |
await execute_planned_task()
        |
await planner.run()
        |
await MCP tool execution
'''
