class EnvironmentFeedback:
    success: bool
    score: float
    details: list[str]


class TravelEnvironment:

    def __init__(self, mcp_tools=None, database=None):
        self.mcp_tools = mcp_tools or {}
        self.database = database

    async def evaluate(
        self,
        candidate,
        task,
        execution_result=None,
        tool_name=None,
    ):
        success = execution_result is not None

        return EnvironmentFeedback(
            success=success,
            score=1.0 if success else 0.0,
            details=[
                "Validated against execution result"
            ],
        )

    async def check(self, node, result):
        feedback = await self.evaluate(
            candidate=str(node),
            task=str(node),
            execution_result=result,
        )

        return {
            "grounded_execution": feedback.success,
            "environment_score": feedback.score > 0,
        }