"""Small durable HITL helper for the refund graph.

The graph pauses at ``hitl_approval`` and stores the full state in
GraphCheckpoints. A human decision is persisted before the graph resumes,
so an approval/rejection survives a process restart.
"""

from __future__ import annotations

from typing import Any

from state_graph.checkpointer import load_checkpoint, save_checkpoint

GRAPH_NAME = "refund_graph"
HITL_NODE = "hitl_approval"


class HITLError(ValueError):
    """Raised when a HITL decision cannot be applied to a run."""


def apply_human_decision(
    run_id: str,
    approved: bool,
    *,
    approver_id: int | None = None,
    reason: str = "",
) -> dict[str, Any]:
    """Persist a human approval/rejection for a paused refund run.

    This is the function your UI/admin endpoint should call when the human
    clicks Approve or Reject. It does not continue the graph; call
    ``resume_run(run_id)`` afterwards.
    """
    if not isinstance(approved, bool):
        raise HITLError("approved must be True or False.")

    checkpoint = load_checkpoint(run_id)
    if checkpoint is None:
        raise HITLError(f"No checkpoint found for run_id={run_id}")

    if checkpoint["graph_name"] != GRAPH_NAME:
        raise HITLError(
            f"Run {run_id} belongs to graph {checkpoint['graph_name']!r}, "
            f"not {GRAPH_NAME!r}."
        )

    if checkpoint["current_node"] != HITL_NODE:
        raise HITLError(
            f"Run {run_id} is not waiting for HITL approval; "
            f"current node is {checkpoint['current_node']!r}."
        )

    state = {
        **checkpoint["state"],
        "human_decision": approved,
        "approval_status": "approved" if approved else "rejected",
    }

    if approver_id is not None:
        state["approver_id"] = int(approver_id)

    if reason.strip():
        state["approval_reason"] = reason.strip()

    save_checkpoint(
        run_id=run_id,
        graph_name=GRAPH_NAME,
        current_node=HITL_NODE,
        state=state,
        status="paused_hitl",
    )

    return state
