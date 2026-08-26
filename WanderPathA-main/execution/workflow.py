from execution.executor import execute_plan


class ExecutionWorkflow:

    def __init__(
        self,
        tool_registry,
    ):

        self.tool_registry = tool_registry


    async def run(
        self,
        execution_state,
    ):

        return await execute_plan(
            execution_state,
            self.tool_registry,
        )
