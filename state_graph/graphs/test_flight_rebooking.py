"""
state_graph/graphs/test_flight_rebooking.py

Reproducible test script for the flight-rebooking graph (Issue #2/#3).
Owner: Person 1

Run this directly (from inside state_graph/graphs/, or from the
project root - see note at the bottom) to verify the full graph works
end to end against the live MySQL checkpointer:

    python state_graph/graphs/test_flight_rebooking.py

This exercises:
  1. A full "refund" path (auto-approved, low amount).
  2. A full "refund" path that hits HITL (amount above threshold),
     then resumes after simulated admin approval.
  3. A "rebook" path that gets rejected once by the airline (the
     CYCLE), then approved on the second attempt.
  4. A customer who never responds, landing on HITL #1.

Each scenario prints the final node/status so you can see the graph
actually paused where it was supposed to and resumed correctly.
"""

import sys
import os
import uuid

# Allow running this file directly from state_graph/graphs/ by adding
# the project root to the path, so `state_graph.graphs.X` imports work
# the same way they do when run from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from state_graph.graphs.flight_rebooking import start_run, resume_run
from state_graph.checkpointer import save_checkpoint, load_checkpoint


def scenario_refund_auto_approved():
    print("=" * 60)
    print("SCENARIO 1: Refund under threshold - auto-approved")
    print("=" * 60)

    run_id = f"test-refund-auto-{uuid.uuid4()}"
    result = start_run(
        run_id,
        {
            "flight_id": 101,
            "customer_id": 1,
            "customer_is_vip": False,
            "refund_amount": 200.0,
        },
    )
    # The graph pauses at awaiting_customer_response first - simulate
    # the customer replying "refund", then resume.
    print(f"  Paused at: {result['final_node']} (expected: awaiting_customer_response)")
    assert result["final_node"] == "awaiting_customer_response"

    # Simulate the platform recording the customer's reply.
    state = result["state"]
    state["customer_response"] = "refund"
    save_checkpoint(run_id, "flight_rebooking", "awaiting_customer_response", state)

    result = resume_run(run_id)
    print(f"  Final node: {result['final_node']}, status: {result['status']}")
    print(f"  Outcome: {result['state']['final_outcome']}")
    print(f"  Cited policy: {result['state']['refund_decision']['cited_policy_ids']}")
    assert result["final_node"] == "end"
    assert result["state"]["final_outcome"] == "refunded_auto"
    print("  PASSED\n")


def scenario_refund_hitl():
    print("=" * 60)
    print("SCENARIO 2: Refund over threshold - needs HITL approval")
    print("=" * 60)

    run_id = f"test-refund-hitl-{uuid.uuid4()}"
    result = start_run(
        run_id,
        {
            "flight_id": 102,
            "customer_id": 2,
            "customer_is_vip": False,
            "refund_amount": 750.0,
        },
    )
    state = result["state"]
    state["customer_response"] = "refund"
    save_checkpoint(run_id, "flight_rebooking", "awaiting_customer_response", state)

    result = resume_run(run_id)
    print(f"  Paused at: {result['final_node']} (expected: hitl_refund_approval)")
    assert result["final_node"] == "hitl_refund_approval"
    assert result["status"] == "paused_hitl"

    # Simulate an admin approving the refund through the platform.
    state = result["state"]
    state["refund_approved"] = True
    save_checkpoint(run_id, "flight_rebooking", "hitl_refund_approval", state)

    result = resume_run(run_id)
    print(f"  Final node: {result['final_node']}, status: {result['status']}")
    print(f"  Outcome: {result['state']['final_outcome']}")
    assert result["state"]["final_outcome"] == "refunded_approved"
    print("  PASSED\n")


def scenario_rebook_with_cycle():
    print("=" * 60)
    print("SCENARIO 3: Rebooking - airline rejects once, then confirms (CYCLE)")
    print("=" * 60)

    run_id = f"test-rebook-cycle-{uuid.uuid4()}"
    result = start_run(
        run_id,
        {
    "flight_id": 3,
    "customer_id": 3,
    "customer_is_vip": True,
    "connected_services": ["hotel_transfer"],
    "origin_airport": "DXB",
    "destination_airport": "LHR",
    "departure_date": "2026-08-03",
},
    )
    state = result["state"]
    state["customer_response"] = "rebook"
    save_checkpoint(run_id, "flight_rebooking", "awaiting_customer_response", state)

    result = resume_run(run_id)
    print(f"  Paused at: {result['final_node']} (expected: awaiting_airline_response)")
    assert result["final_node"] == "awaiting_airline_response"
    print(f"  Decomposition plan created: {[s['step'] for s in result['state']['rebooking_plan']]}")

    # Simulate the airline REJECTING the first proposed alternative.
    state = result["state"]
    state["airline_response"] = "rejected"
    save_checkpoint(run_id, "flight_rebooking", "awaiting_airline_response", state)

    result = resume_run(run_id)
    print(f"  After rejection, paused at: {result['final_node']} (expected: awaiting_airline_response again - the cycle)")
    assert result["final_node"] == "awaiting_airline_response"
    assert len(result["state"]["alternatives_tried"]) == 1

    # Simulate the airline CONFIRMING the second attempt.
    state = result["state"]
    state["airline_response"] = "confirmed"
    save_checkpoint(run_id, "flight_rebooking", "awaiting_airline_response", state)

    result = resume_run(run_id)
    print(f"  Final node: {result['final_node']}, status: {result['status']}")
    print(f"  Outcome: {result['state']['final_outcome']}")
    print(f"  Alternatives tried before success: {len(result['state']['alternatives_tried'])}")
    assert result["state"]["final_outcome"] == "rebooked"
    print("  PASSED - cycle confirmed working\n")


def scenario_customer_no_response():
    print("=" * 60)
    print("SCENARIO 4: Customer never replies - HITL #1")
    print("=" * 60)

    run_id = f"test-no-response-{uuid.uuid4()}"
    result = start_run(
        run_id,
        {
            "flight_id": 104,
            "customer_id": 4,
            "customer_is_vip": False,
        },
    )
    print(f"  Paused at: {result['final_node']} (expected: awaiting_customer_response)")
    assert result["final_node"] == "awaiting_customer_response"

    # Simulate the 24h timeout being recorded (e.g. by a scheduled job).
    state = result["state"]
    state["customer_response"] = "timeout_no_reply"
    save_checkpoint(run_id, "flight_rebooking", "awaiting_customer_response", state)

    result = resume_run(run_id)
    print(f"  Final node: {result['final_node']}, status: {result['status']}")
    assert result["final_node"] == "hitl_no_response"
    assert result["status"] == "paused_hitl"
    print("  PASSED - correctly escalated to a human instead of auto-rebooking\n")


def scenario_crash_and_resume():
    print("=" * 60)
    print("SCENARIO 5: Crash-and-resume proof (manual check)")
    print("=" * 60)
    run_id = f"test-crash-{uuid.uuid4()}"
    start_run(
        run_id,
        {"flight_id": 105, "customer_id": 5, "customer_is_vip": False},
    )
    print(f"  Run started and checkpointed. run_id = {run_id}")
    print(
        "  To prove crash-and-resume manually:\n"
        "  1. Note the run_id above.\n"
        "  2. Kill this process now (Ctrl+C).\n"
        "  3. In a new Python session, run:\n"
        f"       from state_graph.checkpointer import load_checkpoint\n"
        f"       load_checkpoint('{run_id}')\n"
        "  4. Confirm it returns current_node='awaiting_customer_response'\n"
        "     with no data loss, proving the checkpoint survived.\n"
    )


if __name__ == "__main__":
    scenario_refund_auto_approved()
    scenario_refund_hitl()
    scenario_rebook_with_cycle()
    scenario_customer_no_response()
    scenario_crash_and_resume()

    print("=" * 60)
    print("ALL SCENARIOS PASSED")
    print("=" * 60)