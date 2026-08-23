"""
execution/executor.py

Executes the selected execution plan.

Flow

Execution Plan
      |
      v
Run Task
      |
      v
Save Checkpoint
      |
      v
Next Task
      |
      v
Complete Checkpoint
"""

from execution.task_runner import execute_task

from state_graph.checkpointer import (
    save_checkpoint,
    complete_checkpoint,
)


async def execute_plan(
    execution_state,
    tool_registry,
):
    """
    Execute every task in the execution plan.

    After each successful task a checkpoint is stored,
    allowing workflow recovery after crashes or restarts.
    """

    results = {}

    for task in execution_state.tasks:

        # Execute one task
        task = await execute_task(
            task,
            tool_registry,
        )

        # Store task result
        results[task.tool_name] = {
            "status": task.status,
            "result": task.result,
            "error": task.error,
        }

        # Advance execution progress
        execution_state.current_step += 1

        # Save checkpoint
        save_checkpoint(
            run_id=execution_state.run_id,
            graph_name="vip_trip_customization",
            current_node=task.tool_name,
            state=execution_state.__dict__,
        )

        # Optional: stop execution if a task failed
        if task.status == "failed":
            execution_state.completed = False

            return results

    # Mark workflow completed
    execution_state.completed = True

    # Final checkpoint
    complete_checkpoint(
        run_id=execution_state.run_id,
        graph_name="vip_trip_customization",
        current_node="workflow_completed",
        state=execution_state.__dict__,
    )

    return results
