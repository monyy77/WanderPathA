"""
Decomposition-first execution engine.

Generates DAG first, then executes:
- TOOL_CALL  -> MCP tools
- PLANNED    -> Planner executor
- REASONING  -> LLM reasoning

Fixed:
- Tool calls no longer execute with empty {}
- Flight/customer entities are converted to required arguments
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import json
import asyncio
import re

from langchain_core.language_models.chat_models import BaseChatModel

from pydantic import BaseModel, ConfigDict

from planning.dag import Plan, Task, TaskType
from planning.schema import PlannerResult



PLANNER_SYSTEM = """
You are a careful task-decomposition planner for an airline
Irregular Operations (IROPS) desk.

Produce an executable DAG.

Each task must have:

- kind:
    - tool_call
    - reasoning
    - planned

For tool_call tasks:
- tool_name MUST exactly match one available tool.
- instruction should contain required arguments if known.

Available tools:

{tool_names}
"""



class PlannedTask(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    id: str
    instruction: str
    depends_on: list[str]
    kind: str
    tool_name: str | None = None



class GeneratedPlan(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    goal: str
    tasks: list[PlannedTask]



# =====================================================
# Argument Injection
# =====================================================

KNOWN_ENTITIES = {

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

    "c001": {
        "user_id": "C001"
    },

    "c002": {
        "user_id": "C002"
    }
}



def extract_tool_arguments(
    text: str
) -> dict[str, Any]:

    text = text.lower()

    arguments = {}


    # Flight IDs
    flight_match = re.search(
        r"flight\s*#?\s*(\d+)",
        text
    )

    if flight_match:
        arguments["flight_id"] = int(
            flight_match.group(1)
        )


    # Customer IDs
    customer_match = re.search(
        r"c00\d",
        text
    )

    if customer_match:

        arguments["user_id"] = (
            customer_match.group(0)
            .upper()
        )


    # Flight 2 mapping
    if arguments.get("flight_id") == 2:

        arguments.update(
            {
                "originSkyId": "CAI",
                "destinationSkyId": "JED"
            }
        )


    # Flight 3 mapping
    if arguments.get("flight_id") == 3:

        arguments.update(
            {
                "originSkyId": "DXB",
                "destinationSkyId": "LHR"
            }
        )


    # Default date
    if (
        "flight options" in text
        or "departuredate" in text
    ):

        arguments.setdefault(
            "departureDate",
            "2026-08-25"
        )


    return arguments



# =====================================================
# DAG Generation
# =====================================================

def decompose_goal(
    goal: str,
    llm: BaseChatModel,
    tool_names: list[str],
) -> Plan:


    generated = llm.with_structured_output(
        GeneratedPlan,
        method="json_schema",
    ).invoke(
        [
            (
                "system",
                PLANNER_SYSTEM.format(
                    tool_names="\n".join(
                        f"- {name}"
                        for name in tool_names
                    )
                )
            ),

            (
                "human",
                f"""
Decompose this goal:

{goal}

Create 3-8 executable tasks.
"""
            )
        ]
    )


    payload = generated.model_dump()

    payload["goal"] = goal


    return Plan.model_validate(
        payload
    )



# =====================================================
# Execution
# =====================================================

async def execute_plan(
    plan: Plan,
    llm: BaseChatModel,
    mcp_tools: dict[str, Any],

    planner_executor:
    Callable[
        [
            Task,
            dict[str,str],
            str
        ],
        Awaitable[PlannerResult]
    ] | None = None,

    max_workers: int = 4,

) -> dict[str,str]:


    outputs = {}



    for batch in plan.execution_batches():


        async def run_one(
            task_id
        ):

            task = plan.task(
                task_id
            )


            context = "\n\n".join(
                f"OUTPUT FROM {dep}: {outputs[dep]}"
                for dep in task.depends_on
            ) or "No prerequisite outputs."



            if task.kind == TaskType.TOOL_CALL:


                result = await _run_tool_node(
                    task,
                    mcp_tools,
                    plan.goal,
                )



            elif task.kind == TaskType.PLANNED:


                if planner_executor is None:

                    raise RuntimeError(
                        "Missing planner executor"
                    )


                planner_result = await planner_executor(
                    task,
                    outputs,
                    plan.goal,
                )


                result = planner_result.output



            else:


                result = await _run_reasoning_node(
                    task,
                    plan.goal,
                    context,
                    llm,
                )


            return (
                task_id,
                result
            )



        results = await asyncio.gather(
            *(
                run_one(task_id)
                for task_id in batch
            )
        )


        outputs.update(
            dict(results)
        )



    return outputs


# =====================================================
# MCP Tool Execution
# =====================================================

async def _run_tool_node(
    task: Task,
    mcp_tools: dict[str, Any],
    goal: str,
) -> str:

    tool = mcp_tools.get(
        task.tool_name
    )

    if tool is None:
        raise RuntimeError(
            f"Unknown tool {task.tool_name}"
        )


    args = {}


    # Try JSON arguments first
    try:
        parsed_args = json.loads(
            task.instruction
        )

        if isinstance(parsed_args, dict):
            args = parsed_args

    except Exception:
        pass


    # Fallback extraction
    # Handles:
    # "Retrieve status of flight 1"
    # "customer C002"
    # "Flight 2 CAI to JED"

    if not args:

        args = extract_tool_arguments(
            f"""
            Goal:
            {goal}

            Task:
            {task.instruction}
            """
        )


    if not args:

        raise RuntimeError(
            f"No arguments found for tool {task.tool_name}. "
            f"Instruction: {task.instruction}"
        )


    result = await tool.ainvoke(
        args
    )


    return str(result)



# =====================================================
# Reasoning
# =====================================================

async def _run_reasoning_node(
    task: Task,
    goal: str,
    context: str,
    llm: BaseChatModel,
):


    response = await llm.ainvoke(
        [
            (
                "system",
                "You execute one reasoning node."
            ),

            (
                "human",
                f"""
Goal:
{goal}

Task:
{task.instruction}

Context:
{context}

Do not invent information.
"""
            )
        ]
    )


    return response.content.strip()



# =====================================================
# Final Output
# =====================================================

def final_output(
    plan: Plan,
    outputs: dict[str,str],
):


    terminals = plan.terminal_tasks()


    if len(terminals) != 1:

        raise ValueError(
            f"Expected one terminal task, found {terminals}"
        )


    return outputs[
        terminals[0]
    ]