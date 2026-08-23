"""
Decomposition-first: generate the whole DAG up front, in one shot, then
execute it in topological (dependency-safe, batched) order.

FORKED FROM: AmrSheta22/task_decomposition_and_planning
             planning_lab/algorithms/decomposition.py

This module implements the decomposition-first planning strategy:

1. Generate the complete DAG before execution.
2. Inject only available MCP tools.
3. Validate:
   - task kinds
   - tool names
   - DAG structure
4. Execute dependency-safe batches:
   - TOOL_CALL  -> MCP tools
   - PLANNED    -> Planner selector (PS / ToT / LATS)
   - REASONING  -> LLM reasoning node

"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Literal

from langchain_core.language_models.chat_models import BaseChatModel

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from planning.dag import (
    Plan,
    Task,
    TaskType,
)

from planning.schema import PlannerResult



PLANNER_SYSTEM = """
You are a careful task-decomposition planner for an airline's
Irregular Operations (IROPS) desk.

Produce a small executable DAG for reshuffling bookings affected
by a disrupted flight.

Do NOT create a prose checklist.

Every task must contribute directly to the goal.

Independent lookups should have no dependency between them.

The DAG must end with exactly one synthesis task depending on
all required branches.

Each task must have a "kind":

- "tool_call":
    A deterministic operation using exactly one MCP tool.
    Must include "tool_name" from the available tools.

- "reasoning":
    A judgment step using only dependency outputs.
    No new external information.

- "planned":
    A step requiring planning/search because wrong decisions
    have high cost.

Available MCP tools:

{tool_names}
"""



class PlannedTask(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )


    id: str

    instruction: str

    depends_on: list[str]


    kind: Literal[
        "tool_call",
        "reasoning",
        "planned"
    ]


    tool_name: str | None = None


    arguments: dict[str, Any] = Field(
        default_factory=dict
    )



class GeneratedPlan(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )


    goal: str

    tasks: list[PlannedTask]



async def decompose_goal(
    goal: str,
    llm: BaseChatModel,
    tool_names: list[str],
) -> Plan:

    """
    Generate the complete DAG before execution.
    """

    generated = await llm.with_structured_output(
        GeneratedPlan,
        method="json_schema",
    ).ainvoke(
        [
            (
                "system",
                PLANNER_SYSTEM.format(
                    tool_names="\n".join(
                        f"- {name}"
                        for name in tool_names
                    )
                ),
            ),

            (
                "human",
                f"""
Decompose this IROPS goal into 3-8 tasks:

{goal!r}

Rules:

- Use short ids like t1,t2,t3.
- Dependencies must reference existing tasks only.
- Preserve the goal exactly.
""",
            ),
        ],
        temperature=0.1,
    )


    payload = generated.model_dump()

    payload["goal"] = goal



    # Validate generated tasks
    for task in payload["tasks"]:


        if task["kind"] == "tool_call":


            if not task.get("tool_name"):

                raise ValueError(
                    "Tool call task must have tool_name"
                )


            if task["tool_name"] not in tool_names:

                raise ValueError(
                    f"Unknown MCP tool: {task['tool_name']}"
                )


        else:


            if task.get("tool_name"):

                raise ValueError(
                    "Only tool_call tasks can have tool_name"
                )



    plan = Plan.model_validate(
        payload
    )


    # DAG validation if implemented
    if hasattr(plan, "validate_dag"):

        plan.validate_dag()



    return plan




async def execute_plan(
    plan: Plan,

    llm: BaseChatModel,

    mcp_tools: dict[str, Any],

    planner_executor: Callable[
        [
            Task,
            dict[str, str],
            str
        ],
        Awaitable[PlannerResult],
    ] | None = None,

    max_workers: int = 4,

) -> dict[str, str]:


    """
    Execute DAG nodes in dependency-safe batches.

    Execution routing:

        TOOL_CALL
            |
            MCP Tool Registry

        PLANNED
            |
            Planner Selector

        REASONING
            |
            LLM
    """


    outputs: dict[str, str] = {}


    semaphore = asyncio.Semaphore(
        max_workers
    )



    for batch in plan.execution_batches():



        async def run_one(
            task_id: str
        ) -> tuple[str, str]:


            async with semaphore:


                task = plan.task(
                    task_id
                )


                context = "\n\n".join(

                    f"OUTPUT FROM {dependency}:\n"
                    f"{outputs[dependency]}"

                    for dependency in task.depends_on

                ) or "No prerequisite outputs."



                if task.kind == TaskType.TOOL_CALL:



                    if task.tool_name not in mcp_tools:

                        raise RuntimeError(
                            f"Unknown MCP tool in DAG: "
                            f"{task.tool_name}"
                        )


                    result = await _run_tool_node(
                        task,
                        mcp_tools,
                    )



                elif task.kind == TaskType.PLANNED:



                    if planner_executor is None:

                        raise RuntimeError(
                            f"Task {task_id} is planned "
                            "but no planner_executor exists"
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



                return task_id, result




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






async def _run_tool_node(
    task: Task,

    mcp_tools: dict[str, Any],

) -> str:


    tool = mcp_tools.get(
        task.tool_name
    )



    if tool is None:

        raise RuntimeError(
            f"Task {task.id} references unknown tool "
            f"'{task.tool_name}'"
        )



    # Use structured arguments from planner
    args = getattr(
        task,
        "arguments",
        {}
    )



    result = await tool.ainvoke(
        args
    )


    return str(result)






async def _run_reasoning_node(
    task: Task,

    goal: str,

    context: str,

    llm: BaseChatModel,

) -> str:



    prompt = f"""
Overall goal:

{goal}


Current task:

{task.instruction}


Prerequisite outputs:

{context}


Complete only this reasoning task.

Do not invent information.
Use only provided outputs.
"""



    response = await llm.ainvoke(
        [
            (
                "system",
                "You execute one reasoning node in a validated DAG."
            ),

            (
                "human",
                prompt,
            ),
        ],
        temperature=0.2,
    )



    content = response.content



    if not isinstance(content, str) or not content.strip():

        raise RuntimeError(
            "LLM returned empty response"
        )



    return content.strip()






def final_output(
    plan: Plan,

    outputs: dict[str, str],

) -> str:



    terminals = plan.terminal_tasks()



    if len(terminals) != 1:

        raise ValueError(
            "Expected exactly one terminal synthesis task, "
            f"found {terminals}"
        )



    return outputs[
        terminals[0]
    ]



'''
User Goal

        |
        v

Decomposition Planner

        |
        v

MCP Tool Injection

        |
        v

Generate DAG

        |
        v

Validation

        |
        v

Execution Batches


        +----------------+
        |                |
        v                v


   TOOL_CALL        PLANNED

       |                |

       v                v

 MCP Registry     Planner Selector



        |

        v


   REASONING

        |

        v

       LLM
'''
