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
import os
import time

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


from dotenv import load_dotenv

from langchain_core.callbacks import BaseCallbackHandler
from langchain_groq import ChatGroq



from agent.schema import build_agent_step_model
from planning.environment import TravelEnvironment
from planning.planner_selector import PlannerSelector

from planning.plan_and_solve import PlanAndSolvePlanner
from planning.tree_of_thoughts import TreeOfThoughtsPlanner
from planning.lats import LATSPlanner

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

MODEL_NAME = "openai/gpt-oss-20b"


KNOWN_FLIGHT_ARGS = {
    "flight 1": {
        "flight_id": 1
    },
    "flight 2": {
        "flight_id": 2,
        "originSkyId": "CAI",
        "destinationSkyId": "JED"
    },
    "flight 3": {
        "flight_id": 3,
        "originSkyId": "DXB",
        "destinationSkyId": "LHR"
    },
}

def inject_tool_arguments(task, prompt: str) -> str:
    """
    Inject deterministic arguments extracted from task text.
    Prevents MCP calls like get_flight_status({})
    """

    text = (
        f"{task.instruction} {prompt}"
    ).lower()


    for entity, args in KNOWN_FLIGHT_ARGS.items():

        if entity in text:

            prompt += """

Required tool arguments:

"""

            for key, value in args.items():
                prompt += f"{key}={value!r}\n"


            break


    return prompt

# Reused by every prompt that hands the LLM a goal/task instruction so
# tool calls never arrive with empty arguments. Keep entity -> argument
# mappings here in one place instead of re-typing them per call site.
EXECUTION_RULES = """
Important execution rules:

- Every tool call MUST include all required arguments.
- NEVER call tools with empty arguments {}.

Entity mapping:

- Flight 1 -> flight_id=1
- Flight 2 -> flight_id=2, originSkyId="CAI", destinationSkyId="JED"
- Flight 3 -> flight_id=3, originSkyId="DXB", destinationSkyId="LHR"

- Customer C001 -> user_id="C001"
- Customer C002 -> user_id="C002"

If a previous tool output contains a validation error,
do not use it as data.
Retry with corrected arguments.
"""


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
    return ChatGroq(
        model=MODEL_NAME,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
        max_retries=10,
        timeout=120,
    )
    


async def execute_planned_task(
    task,
    outputs,
    goal,
    llm,
    client,
) -> PlannerResult:

    tools = await discover_tools(client)

    tool_registry = MCPToolRegistry(tools)

    environment = TravelEnvironment(
        mcp_client=client
    )

    selector = PlannerSelector(
        llm=llm,
        tool_registry=tool_registry,
        environment=environment,
    )


    planner_type = await selector.select_planner(
        task.instruction
    )


    if planner_type == PlannerType.PLAN_AND_SOLVE:

        planner = PlanAndSolvePlanner(
            llm,
            tool_registry,
        )


    elif planner_type == PlannerType.TREE_OF_THOUGHTS:

        planner = TreeOfThoughtsPlanner(
            llm,
            tool_registry,
        )


    elif planner_type == PlannerType.LATS:

        planner = LATSPlanner(
            llm,
            tool_registry,
            environment,
        )

    else:
        raise ValueError(
            f"Unsupported planner {planner_type}"
        )


    context = "\n\n".join(
        f"OUTPUT FROM {dependency}:\n{outputs[dependency]}"
        for dependency in task.depends_on
    ) or "No prerequisite outputs."



    # ================================
    # FIX: Inject required arguments
    # ================================

    enriched_prompt = f"""
You are executing a travel operations task.

Overall Goal:
{goal}


Current Task:
{task.instruction}


Available MCP Tools:
{list(tools.keys())}

{EXECUTION_RULES}

Known demo data:

Flight IDs:
- Flight 2 = CAI -> JED
- Flight 3 = DXB -> LHR


Customers:
- C001
- C002 (VIP)


If the task mentions Flight 2:
use flight_id=2

If the task mentions Flight 3:
use flight_id=3

If customer profile is required:
use user_id="C002" for VIP cases


Previous Outputs:
{context}


Return the execution result.
"""

    enriched_prompt = inject_tool_arguments(
        task,
        enriched_prompt
        )


    return await planner.run(
        task.id,
        enriched_prompt,
    )


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

        MODEL_NAME
             

    }


    # Every prompt path (decomposition_first and dynamic) gets the same
    # execution rules baked into the goal, so tool calls are grounded in
    # real argument values from the very first LLM call instead of only
    # being patched later inside execute_planned_task.
    goal_with_rules = f"{goal}\n\n{EXECUTION_RULES}"




    if mode == "decomposition_first":


        plan: Plan = decompose_goal(

            goal_with_rules,

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

            goal_with_rules,

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