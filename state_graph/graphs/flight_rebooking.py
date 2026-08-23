"""
state_graph/graphs/flight_rebooking.py

Graph 1: Flight Rebooking & Coordination (Wanderpath) - Issue #2 / #3
Owner: Person 1

WHY THIS IS A STATE GRAPH AND NOT A STRAIGHT-LINE SCRIPT:
- awaiting_customer_response and awaiting_airline_response are genuine
  wait states: the reply may take hours, or may never come at all.
- search_alternatives <-> awaiting_airline_response is a real cycle:
  if the airline rejects a proposed alternative, we go back and search
  again, not just retry the same request.
- Two HITL points exist because two different real-world conditions
  demand a human, not the model, decide: a customer who never replies
  (we don't silently rebook them - that could conflict with their
  actual plans), and a refund above a dollar threshold (financial risk
  needs a human check).

TWO LLM-CALL ADDITIONS FOR THIS GRAPH (Issue #3): Task Decomposition +
RAG. See task_decomposition.py and policy_rag.py for the "why these
two, not the other two" rationale on each node. Short version: this
graph never needs to search over multiple possible plans (no ToT/
LATS - the rebooking sequence is fixed) and never needs a tool-calling
loop at the decision point itself (no constrained ReAct - decisions
here are look-up-and-branch, not act-and-observe).

STATE SHAPE (a plain dict, kept JSON-serializable so it can go straight
into checkpointer.save_checkpoint):
{
    "run_id": str,
    "flight_id": int,
    "customer_id": int,
    "customer_is_vip": bool,
    "customer_response": str | None,     # "rebook" | "refund" | None
    "connected_services": list | None,   # e.g. hotel transfers tied to old flight
    "rebooking_plan": list[dict] | None, # from task_decomposition
    "alternatives_tried": list[dict],
    "proposed_alternative": dict | None,
    "airline_response": str | None,
    "refund_amount": float | None,
    "refund_decision": dict | None,      # from policy_rag
    "refund_approved": bool | None,
    "final_outcome": str | None,
}

HOW RESUME WORKS:
Every node function takes the current state, does its work, and returns
(next_node_name, updated_state). run_graph() saves a checkpoint after
every node. If a node needs a human or an external system, run_graph()
returns immediately instead of looping again - the process can then
die or move on to other work. Later, resume_run(run_id) is called (e.g.
by the platform after an admin acts, or by a webhook handler after the
airline responds) and it picks up from the last saved node.
"""

from typing import Any

from state_graph.checkpointer import save_checkpoint, load_checkpoint
from state_graph.graphs.task_decomposition import (
    decompose_rebooking_task,
    mark_step_done,
)
from tools.booking_tools import get_flight_options
from state_graph.graphs.policy_rag import get_refund_policy_for
import asyncio
from state_graph.mcp_tools import call_mcp_tool

GRAPH_NAME = "flight_rebooking"

# Refund amounts above this require a human to approve (HITL condition
# #2). This number is grounded in policy doc "refund-002" (see
# policy_rag.py) rather than being picked arbitrarily here - refunds
# under this are low-risk enough to automate, above it we want a
# second pair of eyes given the financial impact.
REFUND_HITL_THRESHOLD = 500.0


# ---------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------

def node_flight_disrupted(state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Entry point: a cancellation/delay notice has come in for this
    flight. Nothing to decide here yet, just move forward."""
    return "notify_customer", state


def node_notify_customer(state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Send the customer the rebook-or-refund choice.
    (Actual message sending is a TODO for MCP tool integration -
    Issue #4/#5 once the tool registry work lands. For now this just
    marks that we're waiting.)"""
    # TODO(Issue #5): call the real MCP notification tool here once
    # runtime tool registration exists.
    return "awaiting_customer_response", state


def node_awaiting_customer_response(
    state: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """
    WAIT STATE #1 (genuine external wait).

    This node does NOT decide anything by itself. It only looks at
    what has already been recorded in `state["customer_response"]`.
    That field is set from OUTSIDE this graph - by the platform, when
    the customer actually replies - not by this function guessing.

    If nothing has been recorded yet, we stay here: run_graph() will
    stop looping and the process can exit. Someone must later call
    resume_run() once a response (or a timeout) has been recorded.
    """
    response = state.get("customer_response")

    if response == "rebook":
        return "decompose_rebooking", state
    elif response == "refund":
        return "process_refund", state
    elif response == "timeout_no_reply":
        # Set externally once 24h have passed with no customer reply.
        # We do NOT auto-rebook here - a human decides what happens
        # next, since auto-rebooking without consent could conflict
        # with the customer's actual plans.
        return "hitl_no_response", state
    else:
        # No decision recorded yet - stay paused here.
        return "awaiting_customer_response", state


def node_hitl_no_response(state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    HITL #1: customer didn't respond within the window.
    A human agent decides the next step through the platform. This
    node itself just marks the pause point; run_graph() is the one
    that actually stops execution when it sees this status.
    """
    return "hitl_no_response", state


def node_decompose_rebooking(state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    TASK DECOMPOSITION NODE (Issue #3, addition #1).

    Runs once, the first time we commit to the rebooking path. Builds
    the ordered plan (cancel old booking -> search new flight ->
    rebook connected services -> notify) and stores it in state so it
    survives checkpoint/resume - we don't want to lose the plan and
    re-decompose from scratch if the process crashes mid-run.
    """
    if state.get("rebooking_plan") is None:
        plan = decompose_rebooking_task(state)

    if hasattr(plan, "model_dump"):
        plan = plan.model_dump()
    elif hasattr(plan, "__dict__"):
        plan = plan.__dict__

    state = {**state, "rebooking_plan": plan}
    
    return "search_alternatives", state

def node_search_alternatives(state):
    """Search for a real alternative flight through MCP."""
    import asyncio
    origin = state.get("origin_airport")
    destination = state.get("destination_airport")
    departure_date = state.get("departure_date")

    options = asyncio.run(
        call_mcp_tool(
            "get_flight_options",
            originSkyId=origin,
            destinationSkyId=destination,
            departureDate=departure_date,
        )
    )

    # MCP may return an error object instead of flight options
    if not isinstance(options, list) or (
        options and isinstance(options[0], dict) and "text" in options[0]
    ):
        raise RuntimeError(f"MCP get_flight_options failed: {options}")

    already_tried = {
        alt.get("flight_number")
        for alt in state.get("alternatives_tried", [])
        if alt
    }

    proposed = next(
        (
            opt for opt in options
            if opt.get("flight_number") not in already_tried
        ),
        None,
    )

    if proposed is None:
        state = {
            **state,
            "final_outcome": "no_alternatives_available",
        }
        return "end", state

    state = {
        **state,
        "proposed_alternative": proposed,
    }

    return "awaiting_airline_response", state

def node_awaiting_airline_response(
    state: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """
    WAIT STATE #2 (genuine external wait, driven by a real airline
    system response - not a fixed sleep/timeout).

    Like the customer-response node, this does not guess. It reads
    `state["airline_response"]`, which is set from OUTSIDE this graph
    by a webhook handler when the airline system actually replies.
    """
    airline_response = state.get("airline_response")

    if airline_response == "confirmed":
        return "confirm_rebooking", state
    elif airline_response == "rejected":
        # THE CYCLE: log the rejected attempt and go back to search
        # again, rather than retrying the same request.
        tried = state.get("alternatives_tried", [])
        tried = tried + [state.get("proposed_alternative")]
        state = {
            **state,
            "alternatives_tried": tried,
            "proposed_alternative": None,
            "airline_response": None,  # clear so we wait fresh next time
        }
        return "search_alternatives", state
    else:
        return "awaiting_airline_response", state


def node_confirm_rebooking(state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Terminal success path for the rebooking branch. Marks the
    remaining decomposition steps done."""
    state = mark_step_done(state, "cancel_old_booking")
    if state.get("connected_services"):
        state = mark_step_done(state, "rebook_connected_services")
    state = mark_step_done(state, "notify_customer_of_new_flight")
    state = {**state, "final_outcome": "rebooked"}
    return "end", state


def node_process_refund(state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    RAG NODE (Issue #3, addition #2).

    Decides whether a refund can go through automatically or needs a
    human, GROUNDED in Wanderpath's actual policy documents (see
    policy_rag.py) rather than the model's guess of "typical" airline
    policy. The retrieved policy chunk IDs are stored in state so the
    decision is auditable later (e.g. by an admin reviewing a HITL
    request or a ticket).
    """
    refund_decision = get_refund_policy_for(state)
    state = {**state, "refund_decision": refund_decision}

    if refund_decision["auto_approved"]:
        state = {**state, "final_outcome": "refunded_auto"}
        return "end", state
    else:
        return "hitl_refund_approval", state


def node_hitl_refund_approval(state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    HITL #2: refund above REFUND_HITL_THRESHOLD needs a human agent's
    approval through the platform before it is processed. The agent
    reviewing this can see `state["refund_decision"]["cited_policy_ids"]`
    to know exactly which policy backed the calculation.
    """
    approved = state.get("refund_approved")
    if approved is True:
        state = {**state, "final_outcome": "refunded_approved"}
        return "end", state
    elif approved is False:
        state = {**state, "final_outcome": "refund_denied"}
        return "end", state
    else:
        # Still waiting on the admin's decision - stay paused.
        return "hitl_refund_approval", state


# Nodes that mean "stop looping here, a human or an external system
# must act before we can continue."
PAUSE_NODES = {
    "awaiting_customer_response",
    "awaiting_airline_response",
    "hitl_no_response",
    "hitl_refund_approval",
}

NODE_FUNCTIONS = {
    "flight_disrupted": node_flight_disrupted,
    "notify_customer": node_notify_customer,
    "awaiting_customer_response": node_awaiting_customer_response,
    "hitl_no_response": node_hitl_no_response,
    "decompose_rebooking": node_decompose_rebooking,
    "search_alternatives": node_search_alternatives,
    "awaiting_airline_response": node_awaiting_airline_response,
    "confirm_rebooking": node_confirm_rebooking,
    "process_refund": node_process_refund,
    "hitl_refund_approval": node_hitl_refund_approval,
}


# ---------------------------------------------------------------------
# Graph runner
# ---------------------------------------------------------------------

def _status_for_node(node_name: str) -> str:
    """Maps a node name to the status we record in the checkpoint, so
    the platform's ticket/HITL screens can filter on it later."""
    if node_name == "end":
        return "completed"
    if node_name in ("hitl_no_response", "hitl_refund_approval"):
        return "paused_hitl"
    if node_name in PAUSE_NODES:
        return "waiting_external"
    return "running"


def start_run(run_id: str, initial_state: dict[str, Any]) -> dict[str, Any]:
    """Starts a brand-new graph run from the beginning."""
    state = {"run_id": run_id, **initial_state}
    return _run_graph(run_id, "flight_disrupted", state)


def resume_run(run_id: str) -> dict[str, Any]:
    """
    Resumes an existing run from its last checkpoint.

    This is the function that gets called after:
      - the platform records a customer's reply
      - a webhook records the airline's response
      - an admin approves/denies a HITL request

    It does NOT restart the graph from the top - it reads exactly
    where the run stopped and continues from there, which is the
    whole point of the checkpointing layer from Issue #1.
    """
    checkpoint = load_checkpoint(run_id)
    if checkpoint is None:
        raise ValueError(f"No checkpoint found for run_id={run_id}")

    return _run_graph(run_id, checkpoint["current_node"], checkpoint["state"])


def _run_graph(
    run_id: str, start_node: str, state: dict[str, Any]
) -> dict[str, Any]:
    current_node = start_node

    while True:
        node_fn = NODE_FUNCTIONS[current_node]
        next_node, state = node_fn(state)

        status = _status_for_node(next_node)
        save_checkpoint(
            run_id=run_id,
            graph_name=GRAPH_NAME,
            current_node=next_node,
            state=state,
            status=status,
        )

        if next_node == "end" or next_node in PAUSE_NODES:
            # Either the run is genuinely finished, or it has hit a
            # point that needs an external event/human before it can
            # go any further. Either way, stop looping here.
            return {"final_node": next_node, "status": status, "state": state}

        current_node = next_node