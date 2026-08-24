from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from state_graph.refundGraph.hitl import apply_human_decision
from state_graph.refundGraph.refund_graph import resume_run , resolve_failure_ticket
from state_graph.checkpointer import load_checkpoint, load_history
from shared.database import get_connection

router = APIRouter(prefix="/admin/refunds", tags=["Admin Refund Management"])

class HITLDecisionRequest(BaseModel):
    run_id: str
    approved: bool
    approver_id: int
    reason: Optional[str] = ""


@router.post("/hitl-decision")
async def handle_hitl_decision(payload: HITLDecisionRequest, background_tasks: BackgroundTasks):
    try:
        state = apply_human_decision(
            run_id=payload.run_id,
            approved=payload.approved,
            approver_id=payload.approver_id,
            reason=payload.reason
        )
  
        background_tasks.add_task(resume_run, payload.run_id)
        return {"status": "success", "message": "Decision applied & graph resumed", "state": state}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tickets")
def get_failure_tickets():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT escalation_id, booking_id, employee_id, reason, status, created_date 
        FROM Escalations 
        ORDER BY created_date DESC
    """)
    tickets = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"tickets": tickets}


@router.get("/checkpoints/{run_id}")
def get_run_history(run_id: str):
    history = load_history(run_id)
    latest = load_checkpoint(run_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Run ID not found")
    return {"latest_status": latest["status"], "history": history}

@router.get("/failure-tickets")
def list_failure_tickets():
    """Lists all failure tickets with their status (open/investigating/resolved)."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ticket_id, run_id, failed_node, error_message, status, created_at 
        FROM FailureTickets 
        ORDER BY created_at DESC
    """)
    tickets = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"tickets": tickets}

@router.post("/failure-tickets/{ticket_id}/investigate")
def mark_investigating(ticket_id: int):
    """Sets ticket status to 'investigating'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE FailureTickets SET status = 'investigating' WHERE ticket_id = %s", (ticket_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "investigating"}

@router.post("/failure-tickets/{ticket_id}/resolve")
async def resolve_and_resume_ticket(ticket_id: int, payload: dict, background_tasks: BackgroundTasks):
    """Resolves failure ticket and resumes the graph execution from the failed checkpoint."""
    resolution_notes = payload.get("notes", "Resolved by admin.")
    fixed_state = payload.get("fixed_state", None)
    
    run_id = resolve_failure_ticket(ticket_id, resolution_notes, fixed_state)
    
    # Resume the graph from checkpoint after failure resolution
    background_tasks.add_task(resume_run, run_id)
    return {"status": "resolved", "message": f"Run {run_id} resumed from checkpoint."}