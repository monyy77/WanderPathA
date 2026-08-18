
"""
Decomposition-first: generate the whole DAG up front, in one shot, then
execute it in topological (dependency-safe, batched) order.

FORKED FROM: AmrSheta22/task_decomposition_and_planning
             planning_lab/algorithms/decomposition.py
Credit: `decompose_goal`'s prompt/shape and `execute_plan`'s batching loop
are the toolkit's. What's genuinely different here, because the upstream
version only ever produces plain-text reasoning nodes for a generic demo
goal, and we need real IROPS execution against real MCP tools + the real
DB:

  1. `decompose_goal` asks the planner to tag every node with `kind`
     (tool_call / reasoning / planned) and, for tool_call nodes, a
     `tool_name` drawn from the *actual* set of tools this agent has
     available -- not an open-ended text task.
  2. `execute_plan` no longer sends every node to the LLM. A TOOL_CALL node
     invokes the real MCP tool via `mcp_tools[tool_name]`. A PLANNED node is
     handed off to `planner_executor` (Person 2's concern) instead
     of being solved inline. Only REASONING nodes go straight to the LLM,
     same as upstream.
  3. `final_output` is unchanged (still requires exactly one terminal
     synthesis node -- the toolkit's original constraint, which we keep).

This module is the "decomposition-first" half of the required DAG concern.
See dynamic_decomposition.py for the interleaved half, and
planning_agent.py for the request type + real divergence case between them.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, ConfigDict

from .dag import Plan, Task, TaskType
from .schema import PlannerResult


PLANNER_SYSTEM = """You are a careful task-decomposition planner for an airline's
Irregular Operations (IROPS) desk. Produce a small executable DAG for reshuffling
the bookings affected by a disrupted flight, not a prose checklist. Every task
must make a concrete contribution to the goal. Independent lookups should run in
parallel (no dependency between them). The plan must end with exactly one
synthesis task depending on every necessary branch.

Each task must be tagged with a "kind":
- "tool_call": a single deterministic lookup against one of the tools listed
  below. Must also set "tool_name" to one of those exact names.
- "reasoning": a judgment call made purely from the outputs of its
  dependencies (no new information needed).
- "planned": a step with genuine branching or a real cost to a wrong choice
  (e.g. deciding how to rebook affected passengers). At most one or two
  "planned" tasks per plan -- these are expensive, use them only where
  a single deterministic pass is not safe.

Available tools for "tool_call" tasks:
{tool_names}
"""


class PlannedTask(BaseModel):
    """Wire schema; richer semantic constraints applied by dag.Task."""

    model_config = ConfigDict(extra="forbid")

    id: str
    instruction: str
    depends_on: list[str]
    kind: str
    tool_name: str | None = None


class GeneratedPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str
    tasks: list[PlannedTask]


def decompose_goal(
    goal: str,
    llm: BaseChatModel,
    tool_names: list[str],
) -> Plan:
    """One-shot: ask the LLM for the entire DAG before anything executes."""

    generated = llm.with_structured_output(
        GeneratedPlan,
        method="json_schema",
    ).invoke(
        [
            (
                "system",
                PLANNER_SYSTEM.format(
                    tool_names="\n".join(
                        f"- {name}" for name in tool_names
                    )
                ),
            ),
            (
                "human",
                f"""Decompose this IROPS goal into 3-8 tasks: {goal!r}
Use short task ids such as t1. Dependencies may refer only to tasks in the plan.
Preserve the supplied goal exactly in the plan's goal field.""",
            ),
        ],
        temperature=0.1,
    )

    payload = generated.model_dump()
    payload["goal"] = goal

    return Plan.model_validate(payload)


async def execute_plan(
    plan: Plan,
    llm: BaseChatModel,
    mcp_tools: dict[str, Any],
    planner_executor: Callable[
        [Task, dict[str, str], str],
        Awaitable[PlannerResult],
    ] | None = None,
    max_workers: int = 4,
) -> dict[str, str]:
    """Execute nodes in dependency-safe topological batches.

    Unlike the upstream toolkit (which sends every node straight to the
    LLM), each node is dispatched by its `kind`:

      - TOOL_CALL -> real MCP tool invocation
      - PLANNED   -> handed off to `planner_executor`
                     (Person 2's PS/ToT/LATS selection)
      - REASONING -> plain LLM call over dependency outputs
    """

    import asyncio

    outputs: dict[str, str] = {}

    for batch in plan.execution_batches():

        # Independent nodes in the same generation run concurrently.
        async def run_one(task_id: str) -> tuple[str, str]:
            task = plan.task(task_id)

            context = "\n\n".join(
                f"OUTPUT FROM {dependency}:\n{outputs[dependency]}"
                for dependency in task.depends_on
            ) or "No prerequisite outputs."

            if task.kind == TaskType.TOOL_CALL:

                result = await _run_tool_node(
                    task,
                    mcp_tools,
                )

            elif task.kind == TaskType.PLANNED:

                if planner_executor is None:
                    raise RuntimeError(
                        f"Task {task_id} is 'planned' "
                        "but no planner_executor was supplied"
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
            *(run_one(task_id) for task_id in batch)
        )

        outputs.update(dict(results))

    return outputs


async def _run_tool_node(
    task: Task,
    mcp_tools: dict[str, Any],
) -> str:

    tool = mcp_tools.get(task.tool_name)

    if tool is None:
        raise RuntimeError(
            f"Task {task.id} references unknown tool "
            f"'{task.tool_name}'"
        )

    # `instruction` for a TOOL_CALL node is expected to carry
    # the concrete arguments extracted by the planner.
    # Example: '{"flight_id": 2}'.
    import json

    try:
        args = json.loads(task.instruction)
    except (json.JSONDecodeError, TypeError):
        args = {}

    result = await tool.ainvoke(args)

    return str(result)


async def _run_reasoning_node(
    task: Task,
    goal: str,
    context: str,
    llm: BaseChatModel,
) -> str:

    prompt = f"""Overall goal: {goal}
Current task: {task.instruction}
Prerequisite outputs:
{context}
Complete only the current task. Be concrete and concise. Do not invent data;
rely only on the prerequisite outputs above."""

    response = await llm.ainvoke(
        [
            (
                "system",
                "You execute one reasoning node in a validated task DAG.",
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
            "The chat model returned an empty or unsupported response"
        )

    return content.strip()


def final_output(
    plan: Plan,
    outputs: dict[str, str],
) -> str:

    terminals = plan.terminal_tasks()

    if len(terminals) != 1:
        raise ValueError(
            f"Expected exactly one terminal synthesis task, found {terminals}"
        )

    return outputs[terminals[0]]
