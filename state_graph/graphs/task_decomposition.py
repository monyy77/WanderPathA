"""
state_graph/graphs/task_decomposition.py

Task decomposition for the flight-rebooking graph (Issue #3).
Owner: Person 1

WHY THIS NODE NEEDS TASK DECOMPOSITION (not ToT/LATS/ReAct):
Rebooking a cancelled flight is not one action - it's an ordered
sequence of sub-steps that all have to happen for the customer to
actually be taken care of: cancel the old booking, search for a new
flight, rebook anything connected to the old flight (hotel transfers,
car pickups), and notify the customer. There's no need to search over
multiple possible orderings (that's what Tree of Thoughts/LATS are
for) - the order here is fixed and known in advance. There's also no
external tool-calling loop needed at the decomposition step itself
(that's what constrained ReAct is for) - decomposition just produces
the plan; execution of each step happens elsewhere. That's why
decomposition is the right fit here, not the other three techniques.
"""

from typing import Any


def decompose_rebooking_task(state: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Builds the ordered list of sub-steps needed to fully rebook a
    disrupted flight. This runs once, when we first enter
    search_alternatives, and the resulting plan is stored in the
    graph's state so it survives a checkpoint/resume cycle - we don't
    want to re-decompose the task from scratch after a crash.

    Returns a list of steps, each with a status we update as we go:
        [
            {"step": "cancel_old_booking", "status": "pending"},
            {"step": "search_new_flight", "status": "pending"},
            {"step": "rebook_connected_services", "status": "pending"},
            {"step": "notify_customer_of_new_flight", "status": "pending"},
        ]
    """
    has_connected_services = bool(state.get("connected_services"))

    steps = [
        {"step": "cancel_old_booking", "status": "pending"},
        {"step": "search_new_flight", "status": "pending"},
    ]

    # Only include this step if the booking actually has connected
    # services (e.g. a hotel transfer tied to the old arrival time) -
    # no point planning a step that has nothing to do.
    if has_connected_services:
        steps.append(
            {"step": "rebook_connected_services", "status": "pending"}
        )

    steps.append(
        {"step": "notify_customer_of_new_flight", "status": "pending"}
    )

    return steps


def mark_step_done(state: dict[str, Any], step_name: str) -> dict[str, Any]:
    """Marks one sub-step of the decomposition plan as completed, and
    returns the updated state. Keeping this as a pure function (returns
    a new state rather than mutating) matches how the rest of the graph
    nodes work, so it's safe to call from inside a node."""
    plan = state.get("rebooking_plan", [])
    updated_plan = [
        {**s, "status": "done"} if s["step"] == step_name else s
        for s in plan
    ]
    return {**state, "rebooking_plan": updated_plan}


def all_steps_done(state: dict[str, Any]) -> bool:
    """Checks whether every step in the decomposition plan is done."""
    plan = state.get("rebooking_plan", [])
    return len(plan) > 0 and all(s["status"] == "done" for s in plan)

