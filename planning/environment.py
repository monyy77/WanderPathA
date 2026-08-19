from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EnvironmentFeedback:
    success: bool
    score: float
    details: list[str]


class TravelEnvironment:
    """
    Real execution-based environment for WanderPathA.

    The environment is the source of truth for grounded evaluation.
    It validates:
      1. Tool existence
      2. Tool execution
      3. Execution result
      4. Basic candidate validity for Self-Refine / Reflexion
    """

    def __init__(
        self,
        mcp_tools: dict[str, Any] | None = None,
        database: Any = None,
    ):
        self.mcp_tools = mcp_tools or {}
        self.database = database

    # ============================================================
    # TOOL VALIDATION
    # ============================================================

    def tool_exists(self, tool_name: str | None) -> bool:
        """
        Check whether the requested tool actually exists
        in the currently discovered MCP tool set.
        """

        if not tool_name:
            return False

        return tool_name in self.mcp_tools

    # ============================================================
    # MAIN ENVIRONMENT EVALUATION
    # ============================================================

    async def evaluate(
        self,
        candidate: Any,
        task: str,
        execution_result: Any = None,
        tool_name: str | None = None,
    ) -> EnvironmentFeedback:

        details: list[str] = []

        # --------------------------------------------------------
        # 1. Validate requested tool
        # --------------------------------------------------------

        if tool_name is not None:

            if not self.tool_exists(tool_name):

                return EnvironmentFeedback(
                    success=False,
                    score=0.0,
                    details=[
                        f"Tool '{tool_name}' does not exist "
                        f"in the MCP tool registry."
                    ],
                )

            details.append(
                f"Tool '{tool_name}' exists in MCP registry."
            )

        # --------------------------------------------------------
        # 2. Grounded execution evaluation
        # --------------------------------------------------------

        if execution_result is not None:

            # Explicitly reject obvious execution errors.
            if isinstance(execution_result, Exception):

                return EnvironmentFeedback(
                    success=False,
                    score=0.0,
                    details=[
                        "MCP tool execution failed.",
                        str(execution_result),
                    ],
                )

            # Tool execution happened and returned something.
            details.append(
                "Validated against real MCP tool execution."
            )

            return EnvironmentFeedback(
                success=True,
                score=1.0,
                details=details,
            )

        # --------------------------------------------------------
        # 3. Text candidate evaluation
        #
        # Used by Self-Refine / Reflexion.
        #
        # We cannot claim real tool execution here, so this is
        # deliberately weaker than grounded execution.
        # --------------------------------------------------------

        if candidate is not None and str(candidate).strip():

            details.append(
                "Candidate is non-empty."
            )

            return EnvironmentFeedback(
                success=True,
                score=0.5,
                details=details + [
                    "No MCP execution was provided; "
                    "candidate was only structurally validated."
                ],
            )

        # --------------------------------------------------------
        # 4. Nothing to evaluate
        # --------------------------------------------------------

        return EnvironmentFeedback(
            success=False,
            score=0.0,
            details=[
                "No executable result or valid candidate was provided."
            ],
        )

    # ============================================================
    # LATS COMPATIBILITY CHECK
    # ============================================================

    async def check(
        self,
        node: Any,
        result: Any,
    ) -> dict[str, bool]:

        tool_name = getattr(node, "tool", None)

        feedback = await self.evaluate(
            candidate=str(node),
            task=str(getattr(node, "thought", node)),
            execution_result=result,
            tool_name=tool_name,
        )

        return {
            "grounded_execution": feedback.success,
            "environment_score": feedback.score > 0,
        }