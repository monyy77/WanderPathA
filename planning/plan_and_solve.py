import json

from typing import Any

from planning.schema import (
    PlannerResult,
    PlannerType
)

from planning.tool_registry import MCPToolRegistry


def _clean_json_response(content: str) -> str:
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()
class PlanAndSolvePlanner:


    def __init__(
        self,
        llm,
        tool_registry: MCPToolRegistry
    ):

        self.llm = llm
        self.tool_registry = tool_registry

    def _available_tool_names(self) -> list[str]:
        """
        Return the real MCP tool names available to this planner.
        """

        registry = self.tool_registry

        if hasattr(registry, "tools"):
            tools = registry.tools
        elif hasattr(registry, "registry"):
            tools = registry.registry
        else:
            return []

        if isinstance(tools, dict):
            return sorted(tools.keys())

        return sorted(
            tool.name
            for tool in tools
            if hasattr(tool, "name")
        )

    async def create_plan(
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
        available_tools = self._available_tool_names()

        tools_text = "\n".join(
            f"- {name}"
            for name in available_tools
        )

        prompt = f"""
        You are a planning agent.

        Task:
        {task}


        REAL MCP TOOLS AVAILABLE:
        {tools_text}

        IMPORTANT RULES:

        1. You MUST use ONLY tools from the REAL MCP TOOLS AVAILABLE list.
        2. NEVER invent, rename, or assume a tool.
        3. The "tool" field MUST exactly match one of the listed tool names.
        4. If one operation is not directly available, compose it using
        multiple available tools.
        5. Do not use examples such as search_flights unless that exact
        tool exists in the available list.
        6. Return ONLY a valid JSON array.
        7. Do not include markdown or explanations.

        Create a step-by-step execution plan.


        Format:

        [
          {{
            "step": "Check the current flight status",
            "tool": "get_flight_status",
            "args": {{
            "flight_id": "3"
            }}
          }}
        ]

        """


        response =  self.llm.invoke(
            prompt
        )


        try:
            cleaned = _clean_json_response(response.content)
            return json.loads(cleaned)


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
        resolved_name = tool_name
        if hasattr(self.tool_registry, "_resolve_tool_name"):
            resolved_name = self.tool_registry._resolve_tool_name(tool_name)

        available_tools = set(self._available_tool_names())
        
        available_tools = set(
            self._available_tool_names()
        )

        if tool_name not in available_tools:
            return {
                "success": False,
                "tool": tool_name,
                "error": (
                    f"Unknown MCP tool '{tool_name}'. "
                    f"Available tools: {sorted(available_tools)}"
                ),
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

        plan = await self.create_plan(
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
