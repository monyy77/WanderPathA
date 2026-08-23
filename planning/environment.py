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
      4. Candidate quality for Self-Refine / Reflexion


    Used by:

        Planner
          |
          |
        LATS
          |
          |
        Environment


        Self-Refine
          |
          |
        Environment


        Reflexion
          |
          |
        Environment
    """



    def __init__(
        self,
        mcp_tools: dict[str, Any] | None = None,
        database: Any = None,
        mcp_client: Any = None,
    ):

        """
        Initialize execution environment.

        Args:

            mcp_tools:
                Discovered MCP tools registry.

            database:
                Optional database handle.

            mcp_client:
                Optional MCP client compatibility field.
        """


        self.mcp_tools = (
            mcp_tools
            or {}
        )


        self.database = database


        self.mcp_client = mcp_client



    # ============================================================
    # TOOL VALIDATION
    # ============================================================


    def tool_exists(
        self,
        tool_name: str | None,
    ) -> bool:

        """
        Check whether a requested tool exists
        inside the discovered MCP tool set.
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


            if not self.tool_exists(
                tool_name
            ):


                return EnvironmentFeedback(

                    success=False,

                    score=0.0,

                    details=[

                        f"Tool '{tool_name}' does not exist "
                        "in MCP tool registry."

                    ],

                )


            details.append(

                f"Tool '{tool_name}' exists in MCP registry."

            )



        # --------------------------------------------------------
        # 2. Validate real execution result
        # --------------------------------------------------------


        if execution_result is not None:


            if isinstance(
                execution_result,
                Exception,
            ):


                return EnvironmentFeedback(

                    success=False,

                    score=0.0,

                    details=[

                        "MCP tool execution failed.",

                        str(execution_result),

                    ],

                )



            details.append(

                "Validated against real MCP execution."

            )


            return EnvironmentFeedback(

                success=True,

                score=1.0,

                details=details,

            )



        # --------------------------------------------------------
        # 3. Validate generated candidate
        #
        # Used by:
        #   - Self-Refine
        #   - Reflexion
        #
        # No MCP execution exists here.
        # Therefore validation is intentionally weaker.
        # --------------------------------------------------------


        if (
            candidate is not None
            and str(candidate).strip()
        ):


            details.append(

                "Candidate is non-empty."

            )


            return EnvironmentFeedback(

                success=True,

                score=0.5,

                details=details + [

                    "No MCP execution provided; "
                    "candidate was structurally validated."

                ],

            )



        # --------------------------------------------------------
        # 4. Invalid evaluation
        # --------------------------------------------------------


        return EnvironmentFeedback(

            success=False,

            score=0.0,

            details=[

                "No executable result or valid candidate."

            ],

        )





    # ============================================================
    # LATS COMPATIBILITY
    # ============================================================


    async def check(
        self,
        node: Any,
        result: Any,
    ) -> dict[str, bool]:

        """
        Compatibility layer for LATS evaluation.
        """


        tool_name = getattr(
            node,
            "tool",
            None,
        )



        feedback = await self.evaluate(

            candidate=str(node),

            task=str(
                getattr(
                    node,
                    "thought",
                    node
                )
            ),

            execution_result=result,

            tool_name=tool_name,

        )



        return {

            "grounded_execution":
                feedback.success,


            "environment_score":
                feedback.score > 0,

        }

'''
Planning Agent
      |
      |
Discover MCP Tools
      |
      |
MCPToolRegistry
      |
      |
TravelEnvironment
      |
 ┌────┼────────┐
 |    |        |
LATS  Reflexion  Self-Refine
 |
 |
MCP Server
 |
Database
'''
