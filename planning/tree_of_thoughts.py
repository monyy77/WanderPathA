import json

from typing import Any

from planning.plan_and_solve import _clean_json_response
from planning.schema import (
    PlannerResult,
    PlannerType,
    ThoughtNode
)

from planning.tool_registry import MCPToolRegistry


NUM_THOUGHTS = 3


class TreeOfThoughtsPlanner:


    def __init__(
        self,
        llm,
        tool_registry: MCPToolRegistry
    ):

        self.llm = llm
        self.tool_registry = tool_registry



    async def generate_thoughts(
        self,
        subtask: str
    ) -> list[ThoughtNode]:
        """
        Generate multiple reasoning paths.
        """


        prompt = f"""

        You are using Tree of Thoughts reasoning.

        Subtask:

        {subtask}


        Generate {NUM_THOUGHTS} different solutions.


        Each solution must contain:

        - description
        - tool
        - args


        Each solution must represent a genuinely different strategy.

        Avoid producing trivial variations.


        Return ONLY valid JSON array.


        REAL MCP TOOLS:

        {list(self.tool_registry.tools.keys())}


        Use ONLY these tools.

        Never invent a tool name.

        """


        response = await self.llm.ainvoke(
            prompt
        )


        try:

            cleaned = _clean_json_response(
                response.content
            )

            data = json.loads(
                cleaned
            )


            if not isinstance(
                data,
                list
            ):
                return []


        except Exception:

            return []



        thoughts = []


        for i, item in enumerate(data):


            thoughts.append(

                ThoughtNode(

                    id=chr(
                        65 + i
                    ),

                    description=item.get(
                        "description",
                        "No description provided"
                    ),

                    tool=item.get(
                        "tool"
                    ),

                    args=item.get(
                        "args",
                        {}
                    )

                )

            )


        return thoughts





    async def evaluate_thoughts(
        self,
        thoughts: list[ThoughtNode]
    ) -> list[ThoughtNode]:
        """
        Evaluate each branch.
        """


        for thought in thoughts:


            prompt = f"""

            Evaluate this solution:


            {thought.description}


            Give score between 0 and 1.


            Consider:

            - cost

            - efficiency

            - customer preference


            Return ONLY a floating point number.

            Example:

            0.85


            """


            response = await self.llm.ainvoke(
                prompt
            )


            try:

                score_str = (
                    response.content
                    .strip()
                    .replace(
                        "`",
                        ""
                    )
                )


                thought.score = float(
                    score_str
                )


            except Exception:

                thought.score = 0.0



        return thoughts





    def select_best(
        self,
        thoughts: list[ThoughtNode]
    ) -> ThoughtNode:


        if not thoughts:

            raise ValueError(
                "No thoughts available for selection."
            )


        return max(

            thoughts,

            key=lambda x: x.score

        )





    async def execute(
        self,
        thought: ThoughtNode
    ) -> Any:
        """
        Execute selected branch.
        """


        if not thought.tool:

            return thought.description



        if not self.tool_registry.has_tool(
            thought.tool
        ):

            return (
                f"Tool '{thought.tool}' "
                "is not available in MCP registry."
            )



        return await self.tool_registry.execute(

            thought.tool,

            thought.args

        )





    async def run(
        self,
        task_id: str,
        subtask: str,

    ) -> PlannerResult:


        # 1. Generate branches

        thoughts = await self.generate_thoughts(
            subtask
        )



        if not thoughts:

            return PlannerResult(

                success=False,

                planner=PlannerType.TREE_OF_THOUGHTS,

                task_id=task_id,

                output="No reasoning paths generated"

            )



        # 2. Evaluate branches

        evaluated = await self.evaluate_thoughts(

            thoughts

        )



        # 3. Select best branch

        best = self.select_best(

            evaluated

        )



        # 4. Execute winner

        result = await self.execute(

            best

        )


        tool_calls = []



        if best.tool:

            tool_calls.append(

                {

                    "tool": best.tool,

                    "args": best.args

                }

            )



        return PlannerResult(

            success=True,

            planner=PlannerType.TREE_OF_THOUGHTS,

            task_id=task_id,

            output=str(result),

            tool_calls=tool_calls,


            metadata={


                "all_paths":

                    [

                        {

                            "id": t.id,

                            "description": t.description,

                            "score": t.score

                        }

                        for t in evaluated

                    ],



                "selected_path":

                    best.id,


                "selected_tool":

                    best.tool,


                "selected_score":

                    best.score

            }

        )
