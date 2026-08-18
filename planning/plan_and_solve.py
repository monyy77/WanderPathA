import json

from typing import Any

from planning.schema import (
    PlannerResult,
    PlannerType
)

from planning.tool_registry import MCPToolRegistry



class PlanAndSolvePlanner:


    def __init__(
        self,
        llm,
        tool_registry: MCPToolRegistry
    ):

        self.llm = llm
        self.tool_registry = tool_registry



    def create_plan(
        self,
        task: str
    ) -> list[dict[str, Any]]:
        """
        Generate sequential execution plan.

        Each step contains:
        - step description
        - MCP tool name
        - arguments
        """


        prompt = f"""
        You are a planning agent.

        Task:
        {task}


        Create a step-by-step execution plan.


        Return ONLY valid JSON array.


        Format:

        [
          {{
            "step": "Search available flights",
            "tool": "search_flights",
            "args": {{
                "source": "CAI",
                "destination": "DXB"
            }}
          }}
        ]

        """


        response = self.llm.invoke(
            prompt
        )


        try:

            return json.loads(
                response.content
            )


        except Exception:

            return []



    async def execute_step(
        self,
        step: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute one plan step through MCP Tool Registry.
        """


        tool_name = step.get(
            "tool"
        )

        args = step.get(
            "args",
            {}
        )


        if not tool_name:

            return {
                "success": False,
                "error": "No tool specified"
            }



        try:

            result = await self.tool_registry.execute(
                tool_name,
                args
            )


            return {

                "success": True,

                "tool": tool_name,

                "result": result

            }



        except Exception as e:


            return {

                "success": False,

                "tool": tool_name,

                "error": str(e)

            }



    async def run(
        self,
        task_id: str,
        task: str
    ) -> PlannerResult:
        """
        Generate plan then execute steps sequentially.
        """


        # 1. Generate plan

        plan = self.create_plan(
            task
        )



        if not plan:

            return PlannerResult(

                success=False,

                planner=PlannerType.PLAN_AND_SOLVE,

                task_id=task_id,

                output="Failed to generate execution plan",

                metadata={
                    "reason": "empty_plan"
                }

            )



        execution_results = []

        tool_calls = []

        final_output = ""



        # 2. Execute plan

        for step in plan:


            result = await self.execute_step(step)



            execution_results.append(

                {
                    "step": step,

                    "execution": result

                }

            )



            if step.get("tool"):


                tool_calls.append(

                    {
                        "tool": step["tool"],

                        "args": step.get(
                            "args",
                            {}
                        )

                    }

                )



            if result["success"]:


                final_output += (

                    f"\n{result['result']}"

                )



            else:


                return PlannerResult(

                    success=False,

                    planner=PlannerType.PLAN_AND_SOLVE,

                    task_id=task_id,

                    output="Planning failed during execution",

                    tool_calls=tool_calls,

                    metadata={

                        "failed_step": step,

                        "results": execution_results

                    }

                )



        # 3. Return final result

        return PlannerResult(

            success=True,

            planner=PlannerType.PLAN_AND_SOLVE,

            task_id=task_id,

            output=final_output,

            tool_calls=tool_calls,

            metadata={

                "plan": plan,

                "execution_results": execution_results

            }

        )
