"""
DEPRECATED.

This module is no longer used by the active planning pipeline.

The production execution path is:

planning_agent
    ->
PlannerSelector.execute_planned_task()
    ->
Plan & Solve / Tree of Thoughts / LATS

This file is retained only for backward compatibility and as historical
documentation of the original routing interface used before
planner_selector.py was introduced.
"""

"""
Routing contract for TaskType.PLANNED nodes.

STATUS: superseded by planner_selector.py + execute_planned_task in
planning_agent.py (Person 2's implementation), which route through the
PlannerResult schema (schema.py) instead of the plain-string contract
below. Kept in the repo as the original routing interface this agent's
PLANNED nodes were designed against, and as a minimal fallback path if
Person 2's files are ever unavailable -- not part of the active
execution path once planner_selector.py is wired in.

OWNERSHIP: routing logic itself (PS vs ToT vs LATS selection) is Person
2's concern. This file only defines the interface decomposition.py /
dynamic_decomposition.py originally called into, plus a minimal working
fallback so the pipeline was runnable end-to-end before Person 2's files
landed.

Expected final shape (Person 2 to implement in planner_selector.py,
forked from the toolkit's algorithms/plan_and_solve.py,
tree_of_thoughts.py, lats.py):

    async def route_task(task: Task, outputs: dict[str, str], goal: str) -> str:
        if <task is a single deterministic call with no real alternatives>:
            return await run_plan_and_solve(task, outputs, goal, llm)
        if <task has several plausible orderings/choices worth comparing>:
            return await run_tree_of_thoughts(task, outputs, goal, llm)
        if <task's cost of a wrong choice is high and needs grounded search>:
            return await run_lats(task, outputs, goal, llm, environment)

For this IROPS agent, the concrete routing decision (per the task
description's example) is expected to be:
    - "propose_rebooking_plan" (t5): ToT or LATS -- several valid
      rebooking orderings exist, and a wrong final proposal is expensive
      to unwind.
    - Simpler PLANNED nodes with no real alternatives:
      Plan-and-Solve.

TODO(Person 2): replace `_fallback_route` below with real
PS/ToT/LATS dispatch. Until then this keeps planning_agent.py
runnable for integration testing.
"""

from __future__ import annotations

from typing import Any

from planning.dag import Task


# Optional legacy LLM reference used only by the fallback implementation.
#
# NOTE:
# The active planning pipeline no longer calls configure(), because
# PlannerSelector.execute_planned_task() is now responsible for routing
# every planned node.
#
# This variable exists only so the historical fallback implementation
# remains runnable if someone intentionally revives this module.
_llm: Any = None


def configure(llm: Any) -> None:
    """Configure the legacy fallback LLM.

    This function is no longer used by the production planning pipeline.
    It exists only for backward compatibility with the historical
    planner_router fallback implementation.
    """
    global _llm
    _llm = llm


async def route_task(
    task: Task,
    outputs: dict[str, str],
    goal: str,
) -> str:
    """Dispatch a PLANNED node.

    DEPRECATED:
    The production system routes planned tasks through
    PlannerSelector.execute_planned_task().

    This function is retained only as a compatibility layer.
    """
    return await _fallback_route(task, outputs, goal)


async def _fallback_route(
    task: Task,
    outputs: dict[str, str],
    goal: str,
) -> str:
    """Legacy single-pass planner.

    This is intentionally a minimal fallback implementation and is not
    part of the production execution path.
    """

    if _llm is None:
        raise RuntimeError(
            "planner_router.configure(llm) was never called. "
            "This legacy fallback requires an LLM instance. "
            "The production system should instead use "
            "PlannerSelector.execute_planned_task()."
        )

    context = "\n\n".join(
        f"OUTPUT FROM {dependency}:\n{outputs[dependency]}"
        for dependency in task.depends_on
    ) or "No prerequisite outputs."

    response = await _llm.ainvoke(
        [
            (
                "system",
                "You are a placeholder single-pass planner standing in for "
                "PS/ToT/LATS routing that has not been wired in yet. "
                "Make one careful, concrete decision.",
            ),
            (
                "human",
                f"Overall goal: {goal}\n"
                f"Task: {task.instruction}\n"
                f"Context:\n{context}",
            ),
        ]
    )

    content = response.content

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "The chat model returned an empty or unsupported response."
        )

    return content.strip()
