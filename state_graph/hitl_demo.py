import asyncio
import sys
import time
from dotenv import load_dotenv

from state_graph.refundGraph.refund_graph import start_run, resume_run
from state_graph.refundGraph.hitl import apply_human_decision
from state_graph.checkpointer import load_checkpoint

load_dotenv()


# -------------------------------------------------------------------
# Helper Functions (Refactored from your hitl_demo.py snippet)
# -------------------------------------------------------------------
async def approve_refund(run_id: str = "refund-123"):
    """Applies human approval to a paused run and resumes graph execution."""
    # Note: apply_human_decision is synchronous, so do not use await here
    apply_human_decision(
        run_id=run_id,
        approved=True,
        approver_id=7,
        reason="Refund amount verified against policy.",
    )
    result = await resume_run(run_id)
    return result


async def reject_refund(run_id: str = "refund-123"):
    """Applies human rejection to a paused run and resumes graph execution."""
    # Note: apply_human_decision is synchronous, so do not use await here
    apply_human_decision(
        run_id=run_id,
        approved=False,
        approver_id=7,
        reason="Refund requires additional investigation.",
    )
    result = await resume_run(run_id)
    return result


# -------------------------------------------------------------------
# DEMO 1: HITL Approval and Rejection Flows
# -------------------------------------------------------------------
async def demo_hitl_approval_flow():
    print("\n--- [DEMO 1A] HITL Approval Flow (Amount >= 500) ---")
    run_id = f"demo-hitl-approve-{int(time.time())}"

    # 1. Initialize run with high refund amount to trigger HITL
    print("1. Starting run with amount triggering HITL pause...")
    res = await start_run(
        run_id=run_id,
        initial_state={"booking_id": 101, "employee_id": 5, "amount": 750.0},
    )
    print(f"Graph Status: {res['status']} | Current Node: {res['final_node']}")

    # 2. Verify checkpoint state in the database
    chk = load_checkpoint(run_id)
    print(f"Checkpoint Status in DB: {chk['status']} (Paused as expected)")

    # 3. Apply human approval and resume graph execution
    print("2. Simulating Admin approval from UI...")
    final_res = await approve_refund(run_id=run_id)
    print(
        f"Final Outcome: {final_res['state'].get('final_outcome')} | Status: {final_res['status']}"
    )


async def demo_hitl_rejection_flow():
    print("\n--- [DEMO 1B] HITL Rejection Flow (Amount >= 500) ---")
    run_id = f"demo-hitl-reject-{int(time.time())}"

    print("1. Starting run with amount triggering HITL pause...")
    await start_run(
        run_id=run_id,
        initial_state={"booking_id": 102, "employee_id": 5, "amount": 800.0},
    )

    print("2. Simulating Admin rejection from UI...")
    final_res = await reject_refund(run_id=run_id)
    print(
        f"Final Outcome: {final_res['state'].get('final_outcome')} | Status: {final_res['status']}"
    )


# -------------------------------------------------------------------
# DEMO 2: Failure Ticket Path & Recovery
# -------------------------------------------------------------------
async def demo_ticket_failure_flow():
    print("\n--- [DEMO 2] Ticket / Failure Recovery Flow ---")
    run_id = f"demo-ticket-{int(time.time())}"

    # Initialize a run that triggers external rejection and ToT/Constrained ReAct recovery
    print("1. Starting run that triggers external rejection...")
    res = await start_run(
        run_id=run_id,
        initial_state={
            "booking_id": 999,
            "employee_id": 5,
            "refund_response": "rejected",
        },
    )
    print(f"Final Node: {res['final_node']}")
    print(f"Ticket ID Created: {res['state'].get('ticket_id')}")
    print(f"Final Outcome: {res['state'].get('final_outcome')}")


# -------------------------------------------------------------------
# DEMO 3: Crash-and-Resume (Simulating Process Failure)
# -------------------------------------------------------------------
async def demo_crash_step1():
    run_id = "demo-crash-test"
    print(f"\n--- [DEMO 3 - Step 1] Starting run '{run_id}' and killing process ---")
    await start_run(
        run_id=run_id,
        initial_state={"booking_id": 202, "employee_id": 5, "amount": 600.0},
    )
    print("RUN PAUSED FOR HITL. Simulating Process Crash NOW!")
    sys.exit(0)  # Immediately kill the process to test durable persistence


async def demo_crash_step2():
    run_id = "demo-crash-test"
    print(f"\n--- [DEMO 3 - Step 2] Resuming '{run_id}' after process restart ---")
    
    # Reload state from database checkpoint
    chk = load_checkpoint(run_id)
    print(f"Restored last node from DB: {chk['current_node']}")

    # Approve and resume run after process reboot
    final_res = await approve_refund(run_id=run_id)
    print(
        f"Resumed Successfully! Final Outcome: {final_res['state'].get('final_outcome')}"
    )


# -------------------------------------------------------------------
# Main Execution Entry Point
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Uncomment the scenario you wish to execute/record:
    asyncio.run(demo_hitl_approval_flow())
    # asyncio.run(demo_hitl_rejection_flow())
    # asyncio.run(demo_ticket_failure_flow())

    # --- For Crash Recovery Demo ---
    # 1. Run demo_crash_step1() first (it will exit the process automatically)
    # asyncio.run(demo_crash_step1())
    # 2. Run demo_crash_step2() second to demonstrate recovery from checkpoint
    # asyncio.run(demo_crash_step2())