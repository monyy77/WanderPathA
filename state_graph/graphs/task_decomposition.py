"""
state_graph/graphs/task_decomposition.py

Task decomposition for the flight-rebooking graph (Issue #3).
Owner: Person 1

=== CORRECTION ===
The previous version of this file invented its own hardcoded step list
instead of calling the team's actual decomposition engine
(planning/decomposition.py: decompose_goal), even though this was not
the team's first use of task decomposition. That is fixed here.

WHERE THE LLM COMES FROM: planning/planning_agent.py's build_llm()
(init_chat_model("mistral-large-latest", ...)) is reused directly -
not a new LLM setup. WHERE TOOL NAMES COME FROM: rather than
planning_agent.py's discover_tools() (async, requires a live MCP
client connection - too heavy to invoke from inside a single graph
node), this uses server.tool_registry.list_active_tools(), which is
this project's actual live source of truth for "what tools currently
exist and are active" (Issue #4/#5) and is already synchronous.

WHAT IS STILL NOT CALLED, AND WHY: execute_plan() (also in
planning/decomposition.py) runs every batch of a plan straight through
with no way to pause mid-plan. This graph needs search_new_flight to
be able to stop and wait on the airline's real response for hours,
then resume from a checkpoint - not re-run the whole plan from the
top. So decompose_goal() is reused as-is to PRODUCE the plan, and this
graph's own nodes (in flight_rebooking.py) execute each TOOL_CALL step
one at a time against the real MCP tools, which is what allows
checkpointing between steps.
"""

from typing import Any

from planning.dag import Plan
from planning.decomposition import decompose_goal
from planning.planning_agent import build_llm
from server.tool_registry import list_active_tools


def decompose_rebooking_task(state: dict[str, Any]) -> Plan:
    """
    Builds the real DAG for rebooking a disrupted flight by calling
    the team's actual decompose_goal() - not a hand-written step list.

    This runs once, when we first enter decompose_rebooking. The
    resulting Plan is converted to a plain dict (see plan_to_state_dict)
    and stored in the graph's checkpointed state, so it survives a
    crash/resume cycle without re-calling the LLM.
    """
    flight_id = state.get("flight_id")
    has_connected_services = bool(state.get("connected_services"))

    goal = (
        f"Rebook the customer affected by disrupted flight {flight_id}: "
        f"cancel the old booking, search for a new flight"
        + (
            ", rebook any connected services (e.g. hotel transfers)"
            if has_connected_services
            else ""
        )
        + ", and notify the customer of the new flight."
    )

    llm = build_llm()
    active_tools = list_active_tools(agent_name="flight_rebooking")
    tool_names = [t["tool_name"] for t in active_tools]

    plan = decompose_goal(
    goal=goal,
    llm=llm,
    tool_names=tool_names,
)

    return plan_to_state_dict(plan)

def plan_to_state_dict(plan: Plan) -> list[dict[str, Any]]:
    """
    Converts the real Plan (from decompose_goal) into a plain,
    JSON-serializable list for storage in the checkpointed state -
    Plan/Task are pydantic models with an Enum field (TaskType), which
    needs converting to a plain string before it can go into
    checkpointer.save_checkpoint().
    """
    return [
    {
        "id": task.id,
        "step": task.instruction,
        "depends_on": task.depends_on,
        "kind": task.kind.value,
        "tool_name": task.tool_name,
        "status": "pending",
    }
    for task in plan.tasks
    ]


def mark_step_done(state: dict[str, Any], task_id: str) -> dict[str, Any]:
    """Marks one task in the stored plan as completed, and returns the
    updated state (pure function, matches the rest of the graph's node
    style)."""
    plan = state.get("rebooking_plan", [])
    updated_plan = [
        {**t, "status": "done"} if t["id"] == task_id else t
        for t in plan
    ]
    return {**state, "rebooking_plan": updated_plan}


def get_next_tool_call_task(state: dict[str, Any]) -> dict[str, Any] | None:
    """Finds the next pending TOOL_CALL task in the stored plan - this
    is how flight_rebooking.py's nodes know which real MCP tool to
    call next."""
    plan = state.get("rebooking_plan", [])
    for task in plan:
        if task["kind"] == "tool_call" and task["status"] == "pending":
            return task
    return None


def all_steps_done(state: dict[str, Any]) -> bool:
    """Checks whether every task in the stored plan is done."""
    plan = state.get("rebooking_plan", [])
    return len(plan) > 0 and all(t["status"] == "done" for t in plan)