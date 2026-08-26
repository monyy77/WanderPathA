"""
Refund / Insurance graph

Uses the project's existing pieces :
- state_graph.checkpointer       -> pause/resume + HITL persistence
- state_graph.graphs.policy_rag  -> grounded refund policy
- tools.finance_and_decision_tools -> eligibility / amount / refund
- tools.escalation_tools         -> ticket / human escalation
- planning.tree_of_thoughts      -> appeal/recovery
- agent.schema                    -> constrained ReAct action space

Flow:
START -> CHECK_ELIGIBILITY -> CALCULATE_REFUND -> CHECK_APPROVAL
      -> HITL_APPROVAL -> SUBMIT_REFUND -> COMPLETED

Failure:
CHECK_ELIGIBILITY -> REFUND_REJECTED -> TOT_APPEAL
CHECK_APPROVAL    -> REFUND_REJECTED -> TOT_APPEAL
SUBMIT_REFUND     -> REFUND_REJECTED -> TOT_APPEAL

The graph follows the same checkpoint/resume style already used by
state_graph/graphs/flight_rebooking.py.
"""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_groq import ChatGroq
from state_graph.refundGraph.hitl import apply_human_decision
from agent.schema import build_agent_step_model
from planning.tool_registry import MCPToolRegistry
from planning.tree_of_thoughts import TreeOfThoughtsPlanner
from state_graph.checkpointer import load_checkpoint, save_checkpoint
from state_graph.graphs.policy_rag import get_refund_policy_for
from tools.finance_and_decision_tools import (
    CheckRefundEligibility,
    CalculateRefundAmount,
    ProcessRefund,
    CalculateCompensation,
    IssueTravelVoucher,
)
from tools.escalation_tools import create_support_ticket
from shared.database import get_connection


GRAPH_NAME = "refund_graph"
HITL_THRESHOLD = 500.0

# Only HITL pauses the graph.
PAUSE_NODES = {"hitl_approval"}


def _build_default_llm() -> Any:
    """Default LLM used by start_run/resume_run when the caller doesn't
    supply one, matching the ChatGroq setup used elsewhere in the project."""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
        max_retries=3,
    )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _tool_func(tool: Any) -> Any:
    """Return the underlying callable from a LangChain @tool object."""
    return getattr(tool, "func", tool)


def default_tools() -> dict[str, Any]:
    """Small local registry used when an MCP client is not supplied."""
    return {
        "check_refund_eligibility": CheckRefundEligibility,
        "calculate_refund_amount": CalculateRefundAmount,
        "process_refund": ProcessRefund,
        "calculate_compensation": CalculateCompensation,
        "issue_travel_voucher": IssueTravelVoucher,
        "create_support_ticket": create_support_ticket,
    }


def _call(tool: Any, **kwargs: Any) -> Any:
    """Call a project tool without forcing the graph to depend on MCP."""
    fn = _tool_func(tool)
    return fn(**kwargs)


# ---------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------

def check_eligibility(
    state: dict[str, Any]
) -> tuple[str, dict[str, Any]]:

    booking_id = int(state["booking_id"])

    eligible = bool(
        _call(
            CheckRefundEligibility,
            booking_id=booking_id
        )
    )

    state = {
        **state,
        "eligible": eligible
    }

    if not eligible:
        return "refund_rejected", {
            **state,
            "rejection_reason": (
                "Booking is not eligible for a refund."
            ),
        }

    return "calculate_refund", state


def calculate_refund(
    state: dict[str, Any]
) -> tuple[str, dict[str, Any]]:

    booking_id = int(state["booking_id"])

    amount = float(
        _call(
            CalculateRefundAmount,
            booking_id=booking_id
        )
    )

    # Reuse the existing policy-RAG implementation.
    grounded = get_refund_policy_for(
        {
            **state,
            "refund_amount": amount
        }
    )

    return "check_approval", {
        **state,
        "refund_amount": amount,
        "policy": grounded,
        "cited_policy_ids": grounded["cited_policy_ids"],
    }


def check_approval(
    state: dict[str, Any]
) -> tuple[str, dict[str, Any]]:

    amount = float(state["refund_amount"])

    # Refunds >= $500 require human approval.
    if amount >= HITL_THRESHOLD:
        return "hitl_approval", {
            **state,
            "approval_required": True,
        }

    # Refunds below $500 are automatically approved.
    return "submit_refund", {
        **state,
        "approval_required": False,
        "human_decision": True,
    }


def hitl_approval(
    state: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """
    Pause until a persisted human decision is available.

    Approved -> Submit Refund
    Rejected -> Refund Rejected -> ToT + Agent
    """

    decision = state.get("human_decision")

    if decision is None:
        return "hitl_approval", {
            **state,
            "approval_status": "pending",
        }

    if decision is False:
        return "refund_rejected", {
            **state,
            "approval_status": "rejected",
            "rejection_reason": state.get(
                "approval_reason",
                "Refund was rejected by a human reviewer.",
            ),
        }

    return "submit_refund", {
        **state,
        "approval_status": "approved",
    }


def submit_refund(
    state: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """
    Submit the refund.

    There is no WAITING_RESPONSE node.

    The result of ProcessRefund determines whether the refund
    succeeded or should go to the recovery path.
    """

    result = _call(
        ProcessRefund,
        booking_id=int(state["booking_id"]),
        employee_id=int(state["employee_id"]),
        refund_amount=float(state["refund_amount"]),
    )

    # If ProcessRefund explicitly reports failure,
    # go to the recovery path.
    if isinstance(result, dict):

        success = result.get("success")

        if success is False:
            return "refund_rejected", {
                **state,
                "submit_result": result,
                "rejection_reason": result.get(
                    "reason",
                    "Refund submission failed."
                ),
            }

    # Otherwise submission is successful.
    return "completed", {
        **state,
        "submit_result": result,
        "final_outcome": "refund_completed",
    }


def refund_rejected(
    state: dict[str, Any]
) -> tuple[str, dict[str, Any]]:

    return "tot_appeal", state


# ---------------------------------------------------------------------
# Tree of Thoughts Appeal
# ---------------------------------------------------------------------

async def tot_appeal(
    state: dict[str, Any],
    tool_registry: MCPToolRegistry,
    llm: Any,
) -> tuple[str, dict[str, Any]]:

    """Use ToT to select the safest recovery strategy."""

    recovery_tools = {
        name: tool_registry.tools[name]
        for name in (
            "calculate_compensation",
            "issue_travel_voucher",
            "create_support_ticket",
        )
        if name in tool_registry.tools
    }

    planner = TreeOfThoughtsPlanner(
        llm,
        MCPToolRegistry(recovery_tools),
    )

    task = (
        "A refund was rejected. Determine the safest recovery strategy. "
        "Choose exactly one of: "
        "calculate_compensation, issue_travel_voucher, "
        "create_support_ticket. "
        "Prefer compensation or voucher when appropriate. "
        "Otherwise create a support ticket. "
        f"Booking={state['booking_id']}, "
        f"refund_amount={state.get('refund_amount', 0)}, "
        f"reason={state.get('rejection_reason', 'unknown')}"
    )

    result = await planner.run(
        "refund-appeal",
        task,
    )

    selected_path = result.metadata.get("selected_path")

    return "constrained_react_submit", {
        **state,
        "appeal_result": result.output,
        "appeal_paths": result.metadata.get(
            "all_paths",
            []
        ),
        "selected_path": selected_path,
    }


# ---------------------------------------------------------------------
# Constrained ReAct Recovery
# ---------------------------------------------------------------------

async def constrained_react_submit(
    state: dict[str, Any],
    tool_registry: MCPToolRegistry,
    llm: Any,
) -> tuple[str, dict[str, Any]]:

    """
    Tiny constrained ReAct loop built on the project's Agent schema.

    The model may choose ONLY one of the recovery tools below.
    """

    allowed = {
        "calculate_compensation",
        "issue_travel_voucher",
        "create_support_ticket",
    }

    available = sorted(
        allowed & set(tool_registry.tools)
    )

    if not available:
        return "ticket", {
            **state,
            "failure": "No recovery tools available.",
        }

    selected_path = state.get("selected_path")

    if selected_path not in available:
        return "ticket", {
            **state,
            "failure": (
                f"ToT selected invalid recovery action: "
                f"{selected_path}"
            ),
        }

    model = llm.with_structured_output(
        build_agent_step_model([selected_path])
    )

    prompt = (
        "You are the constrained refund recovery executor. "
        "Execute the recovery strategy selected by the planner. "
        "Do not invent actions.\n"
        f"Allowed actions: {available}\n"
        f"Selected strategy: {selected_path}\n"
        f"Booking ID: {state['booking_id']}\n"
        f"Refund amount: {state.get('refund_amount', 0)}\n"
        f"Rejection: {state.get('rejection_reason', '')}"
    )

    step = await model.ainvoke(prompt)

    args = dict(step.action_input)

    if step.action == "calculate_compensation":

        args = {
            "booking_id": int(
                state["booking_id"]
            )
        }

    elif step.action == "issue_travel_voucher":

        args = {
            "booking_id": int(
                state["booking_id"]
            ),
            "voucher_value": float(
                state.get(
                    "refund_amount",
                    0.0
                )
            ),
        }

    elif step.action == "create_support_ticket":

        args = {
            "booking_id": int(
                state["booking_id"]
            ),
            "employee_id": int(
                state["employee_id"]
            ),
            "issue": state.get(
                "rejection_reason",
                "Refund rejected"
            ),
        }

    try:

        result = await tool_registry.execute(
            step.action,
            args
        )

    except Exception as exc:

        return "ticket", {
            **state,
            "failure": str(exc)
        }

    if step.action == "create_support_ticket":

        return "completed", {
            **state,
            "recovery_action": step.action,
            "recovery_result": result,
            "final_outcome": "ticket_created",
            "ticket_id": (
                result.get("ticket_id")
                if isinstance(result, dict)
                else None
            ),
        }

    return "completed", {
        **state,
        "recovery_action": step.action,
        "recovery_result": result,
        "final_outcome": (
            "recovered_after_refund_rejection"
        ),
    }


# ---------------------------------------------------------------------
# Ticket
# ---------------------------------------------------------------------

def ticket(
    state: dict[str, Any]
) -> tuple[str, dict[str, Any]]:

    """Final failure path; persist a ticket through the existing tool."""

    try:

        result = _call(
            create_support_ticket,
            booking_id=int(
                state["booking_id"]
            ),
            employee_id=int(
                state["employee_id"]
            ),
            issue=(
                state.get("failure")
                or state.get(
                    "rejection_reason",
                    "Refund failure"
                )
            ),
        )

        return "completed", {
            **state,
            "ticket_id": (
                result.get("ticket_id")
                if isinstance(result, dict)
                else None
            ),
            "ticket_result": result,
            "final_outcome": "ticket_created",
        }

    except Exception as exc:

        return "completed", {
            **state,
            "final_outcome": "ticket_pending",
            "failure": str(exc),
        }


# ---------------------------------------------------------------------
# Failure Ticket
# ---------------------------------------------------------------------

def create_failure_ticket(
    run_id: str,
    failed_node: str,
    error: Exception,
    state: dict[str, Any]
) -> int:

    """Creates an unplanned failure ticket and persists current checkpoint."""

    checkpoint_id = save_checkpoint(
        run_id=run_id,
        graph_name="refund_graph",
        current_node=failed_node,
        state={
            **state,
            "last_error": str(error)
        },
        status="failed"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO FailureTickets
        (
            run_id,
            failed_node,
            error_message,
            status,
            checkpoint_id
        )
        VALUES (%s, %s, %s, 'open', %s)
        """,
        (
            run_id,
            failed_node,
            str(error),
            checkpoint_id
        )
    )

    conn.commit()

    ticket_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return ticket_id


def resolve_failure_ticket(
    ticket_id: int,
    resolution_notes: str,
    updated_state: dict[str, Any] = None
) -> str:

    """Updates ticket status to resolved and restores graph checkpoint."""

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM FailureTickets WHERE ticket_id = %s",
        (ticket_id,)
    )

    ticket = cursor.fetchone()

    if not ticket:
        raise ValueError(
            f"Ticket #{ticket_id} not found."
        )

    run_id = ticket["run_id"]

    if updated_state:

        latest_chk = load_checkpoint(run_id)

        new_state = {
            **latest_chk["state"],
            **updated_state
        }

        save_checkpoint(
            run_id=run_id,
            graph_name="refund_graph",
            current_node=ticket["failed_node"],
            state=new_state,
            status="running"
        )

    cursor.execute(
        """
        UPDATE FailureTickets
        SET
            status = 'resolved',
            resolution_notes = %s,
            resolved_at = NOW()
        WHERE ticket_id = %s
        """,
        (
            resolution_notes,
            ticket_id
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    return run_id


# ---------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------

SYNC_NODES = {
    "check_eligibility": check_eligibility,
    "calculate_refund": calculate_refund,
    "check_approval": check_approval,
    "hitl_approval": hitl_approval,
    "submit_refund": submit_refund,
    "refund_rejected": refund_rejected,
    "ticket": ticket,
}


def _status(node: str) -> str:

    if node == "completed":
        return "completed"

    if node in PAUSE_NODES:
        return "paused_hitl"

    return "running"


async def _run(
    run_id: str,
    node: str,
    state: dict[str, Any],
    tool_registry: Any,
    llm: Any,
) -> dict[str, Any]:

    while True:

        try:

            # Async nodes
            if node == "tot_appeal":

                node, state = await tot_appeal(
                    state,
                    tool_registry,
                    llm
                )

            elif node == "constrained_react_submit":

                node, state = await constrained_react_submit(
                    state,
                    tool_registry,
                    llm
                )

            # Sync nodes
            else:

                node, state = SYNC_NODES[node](state)

            status = _status(node)

            save_checkpoint(
                run_id,
                GRAPH_NAME,
                node,
                state,
                status
            )

            if node in PAUSE_NODES or node == "completed":

                return {
                    "final_node": node,
                    "status": status,
                    "state": state
                }

        except Exception as exc:

            # UNPLANNED FAILURE PATH
            ticket_id = create_failure_ticket(
                run_id,
                node,
                exc,
                state
            )

            return {
                "final_node": node,
                "status": "failed",
                "ticket_id": ticket_id,
                "error": str(exc),
                "state": state
            }


# ---------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------

async def start_run(
    run_id: str,
    initial_state: dict[str, Any],
    tools: dict[str, Any] | None = None,
    llm: Any | None = None,
) -> Any:

    """Start a new refund run. Required state: booking_id + employee_id."""

    registry = MCPToolRegistry(
        tools or default_tools()
    )

    model = llm or _build_default_llm()

    state = {
        "run_id": run_id,
        **initial_state
    }

    return await _run(
        run_id,
        "check_eligibility",
        state,
        registry,
        model
    )


async def resume_run(
    run_id: str,
    tools: dict[str, Any] | None = None,
    llm: Any | None = None,
) -> Any:

    """Resume from the latest persisted checkpoint."""

    checkpoint = load_checkpoint(run_id)

    if checkpoint is None:
        raise ValueError(
            f"No checkpoint found for run_id={run_id}"
        )

    registry = MCPToolRegistry(
        tools or default_tools()
    )

    model = llm or _build_default_llm()

    return await _run(
        run_id,
        checkpoint["current_node"],
        checkpoint["state"],
        registry,
        model
    )