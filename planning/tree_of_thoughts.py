import json

from typing import Any

from planning.schema import (
    PlannerResult,
    PlannerType,
    ThoughtNode
)



class TreeOfThoughtsPlanner:


    def __init__(
        self,
        llm,
        tool_registry
    ):

        self.llm = llm
        self.tool_registry = tool_registry



    def generate_thoughts(
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


        Generate 3 different solutions.


        Each solution must contain:

        - description
        - tool
        - args


        Return ONLY valid JSON array.


        Example:

        [
          {{
            "description": "Choose cheapest flight",
            "tool": "search_flights",
            "args": {{
                "sort": "price"
            }}
          }},
          {{
            "description": "Choose fastest flight",
            "tool": "search_flights",
            "args": {{
                "sort": "duration"
            }}
          }}
        ]

        """


        response = self.llm.invoke(
            prompt
        )


        try:

            data = json.loads(
                response.content
            )

        except Exception:

            return []



        thoughts = []


        for i, item in enumerate(data):

            thoughts.append(

                ThoughtNode(

                    id=chr(65+i),

                    description=item["description"],

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



    def evaluate_thoughts(
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

            Return only number.

            """



            response = self.llm.invoke(
                prompt
            )


            try:

                thought.score = float(
                    response.content
                )


            except Exception:

                thought.score = 0.0



        return thoughts



    def select_best(
        self,
        thoughts: list[ThoughtNode]
    ) -> ThoughtNode:


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



        return await self.tool_registry.execute(

            thought.tool,

            thought.args

        )



    async def run(
        self,
        task_id: str,
        subtask: str
    ) -> PlannerResult:


        # 1. Generate branches

        thoughts = self.generate_thoughts(
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

        evaluated = self.evaluate_thoughts(
            thoughts
        )



        # 3. Select best branch

        best = self.select_best(
            evaluated
        )



        # 4. Execute winner

        result = await self.execute(best)

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

                    best.id

            }

        )
