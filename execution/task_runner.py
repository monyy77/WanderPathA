"""
execution/task_runner.py

Executes a single task from the execution plan.

Flow

Task
 |
 v
Validate Tool
 |
 v
Find MCP Tool
 |
 v
Execute Tool
 |
 v
Update Task State
"""

from server.tool_guard import validate_tool


async def execute_task(
    task_state,
    tool_registry,
):
    """
    Execute a single task using the MCP Tool Registry.

    Returns the updated task state.
    """

    # Ensure the tool is allowed by Constrained ReAct
    validate_tool(
        task_state.tool_name
    )

    # Look up the tool in the registry
    tool = tool_registry.get(
        task_state.tool_name
    )

    if tool is None:

        task_state.status = "failed"
        task_state.error = (
            f"Tool '{task_state.tool_name}' not found."
        )

        return task_state

    try:

        # Execute the MCP tool
        result = await tool.ainvoke(
            task_state.input
        )

        task_state.status = "completed"
        task_state.result = result
        task_state.error = None

    except Exception as e:

        task_state.status = "failed"
        task_state.result = None
        task_state.error = str(e)

    return task_state
