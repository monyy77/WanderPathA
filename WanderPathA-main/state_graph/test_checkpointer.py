"""
state_graph/test_checkpointer.py

Reproducible test script for the checkpointing layer (Issue #1).
Owner: Person 1

Run this directly to verify the checkpointer works against the live
MySQL database:

    python state_graph/test_checkpointer.py

It does NOT use pytest on purpose - it's meant to be a simple,
readable script anyone on the team can run and see plain output for,
proving save/load/history all work end to end.
"""

import uuid

from checkpointer import save_checkpoint, load_checkpoint, load_history


def run_test():
    # Use a fresh run_id every time so repeated runs of this script
    # don't collide with each other's data.
    run_id = f"test-run-{uuid.uuid4()}"
    graph_name = "flight_rebooking"

    print(f"Using run_id = {run_id}\n")

    # --- Step 1: save a first checkpoint ---
    print("Step 1: saving first checkpoint (node = start)...")
    save_checkpoint(
        run_id=run_id,
        graph_name=graph_name,
        current_node="start",
        state={"flight_id": 123, "status": "cancelled"},
        status="running",
    )
    print("  OK\n")

    # --- Step 2: save a second checkpoint, simulating progress ---
    print("Step 2: saving second checkpoint (node = searching_alternatives)...")
    save_checkpoint(
        run_id=run_id,
        graph_name=graph_name,
        current_node="searching_alternatives",
        state={
            "flight_id": 123,
            "status": "cancelled",
            "alternatives_found": 3,
        },
        status="running",
    )
    print("  OK\n")

    # --- Step 3: load the latest checkpoint and verify it's step 2 ---
    print("Step 3: loading latest checkpoint...")
    latest = load_checkpoint(run_id)
    assert latest is not None, "Expected a checkpoint, got None"
    assert latest["current_node"] == "searching_alternatives", (
        f"Expected node 'searching_alternatives', got '{latest['current_node']}'"
    )
    assert latest["state"]["alternatives_found"] == 3
    print(f"  OK - latest node is '{latest['current_node']}', "
          f"state = {latest['state']}\n")

    # --- Step 4: load full history and verify both checkpoints are there ---
    print("Step 4: loading full history...")
    history = load_history(run_id)
    assert len(history) == 2, f"Expected 2 checkpoints, got {len(history)}"
    print(f"  OK - found {len(history)} checkpoints in order:")
    for row in history:
        print(f"    - {row['current_node']} -> {row['state']}")

    # --- Step 5: load a checkpoint for a run_id that never existed ---
    print("\nStep 5: loading a checkpoint for a run_id that doesn't exist...")
    missing = load_checkpoint("this-run-id-does-not-exist")
    assert missing is None, "Expected None for a missing run_id"
    print("  OK - correctly returned None\n")

    print("=" * 50)
    print("ALL CHECKS PASSED")
    print("=" * 50)
    print(
        "\nTo test crash-and-resume manually:\n"
        "1. Run this script but comment out Step 2 temporarily.\n"
        "2. Note the run_id printed above.\n"
        "3. Kill this process (Ctrl+C) right after Step 1 finishes.\n"
        "4. In a new run, call load_checkpoint(run_id) with that same\n"
        "   run_id and confirm you get back the 'start' node state -\n"
        "   proving the checkpoint survived the crash.\n"
    )


if __name__ == "__main__":
    run_test()