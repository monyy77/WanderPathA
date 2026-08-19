from __future__ import annotations

from typing import Any

from planning.decomposition import execute_plan, final_output
from planning.environment import TravelEnvironment


class PlanningExecutionPipeline:
    """
    Connects the planning layer with the grounded execution environment.

    Flow:

        Planner
           ↓
        DAG / Plan
           ↓
        MCP execution
           ↓
        Grounded Environment
           ↓
        EnvironmentFeedback
    """

    def __init__(
        self,
        llm: Any,
        mcp_tools: dict[str, Any],
    ):
        self.llm = llm
        self.mcp_tools = mcp_tools

        self.environment = TravelEnvironment(
            mcp_tools=mcp_tools,
        )

    async def execute_plan(
        self,
        plan,
    ):
        """
        Execute the generated plan using the real MCP tools.
        """

        outputs = await execute_plan(
            plan=plan,
            llm=self.llm,
            mcp_tools=self.mcp_tools,
        )

        result = final_output(
            plan,
            outputs,
        )

        return result, outputs

    async def evaluate_result(
        self,
        result: str,
        task: str | None = None,
    ):
        """
        Evaluate the final planner result against
        the grounded environment.
        """

        return await self.environment.evaluate(
            candidate=result,
            task=task,
        )

    async def run(
        self,
        plan,
    ):
        """
        Full integration pipeline.

        Plan
          ↓
        Execute
          ↓
        Evaluate
        """

        result, outputs = await self.execute_plan(
            plan
        )

        feedback = await self.evaluate_result(
            result=result,
            task=plan.goal,
        )

        return {
            "result": result,
            "outputs": outputs,
            "feedback": feedback,
        }