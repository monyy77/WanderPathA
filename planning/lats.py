from planning.schema import (
    PlannerResult,
    PlannerType,
    LATSNode
)

from langchain_core.utils.json import parse_json_markdown


class LATSPlanner:

    def __init__(
        self,
        llm,
        tool_registry,
        environment
    ):

        self.llm = llm
        self.tool_registry = tool_registry
        self.environment = environment

        self.available_tools = (
            self._available_tool_names()
        )



    async def expand(
        self,
        node: LATSNode
    ):
        """
        Generate multiple possible next actions.
        Tree Expansion step.
        """

        self.available_tools = (
            self._available_tool_names()
        )


        if not self.available_tools:
            raise RuntimeError(
                "No MCP tools available for LATS planner"
            )


        prompt = f"""

Current state:

{node.thought}


Available MCP tools:

{chr(10).join(
    "- " + tool
    for tool in self.available_tools
)}


Generate 3 possible next actions.


IMPORTANT:

1. The "tool" field MUST be exactly one of the available MCP tools.

2. NEVER invent tools.

3. Every action MUST use exactly one MCP tool.

4. Arguments must match the selected tool.


Return ONLY valid JSON.


Example:

[
  {{
    "description": "Search available flights",
    "tool": "search_flights",
    "args": {{
        "sort": "price"
    }}
  }}
]

"""


        response = await self.llm.ainvoke(
            prompt
        )


        try:

            responses = parse_json_markdown(
                response.content
            )


            if not isinstance(
                responses,
                list
            ):
                responses = []


            responses = [
                item
                for item in responses
                if isinstance(
                    item,
                    dict
                )
                and item.get("tool")
                in self.available_tools
            ]


        except Exception:

            responses = []



        for index, item in enumerate(responses):

            child = LATSNode(

                id=f"{node.id}-{index}",

                thought=item.get(
                    "description",
                    ""
                ),

                parent=node,

                tool=item.get(
                    "tool"
                ),

                args=item.get(
                    "args",
                    {}
                )
            )


            node.children.append(
                child
            )


        node.expanded = True


        return node.children




    async def execute_node(
        self,
        node: LATSNode
    ):
        """
        Execute selected action using MCP Tool Registry.
        """


        # Refresh registry
        self.available_tools = (
            self._available_tool_names()
        )


        if not node.tool:

            raise ValueError(
                "LATS generated a node without MCP tool"
            )


        if node.tool not in self.available_tools:

            raise ValueError(
                f"LATS generated unknown MCP tool: {node.tool}"
            )


        return await self.tool_registry.execute(
            node.tool,
            node.args
        )




    def calculate_reward(
        self,
        feedback
    ):
        """
        Calculate reward from environment feedback.
        """


        if not feedback:

            return 0.0



        if hasattr(
            feedback,
            "score"
        ):

            return float(
                feedback.score
            )



        if hasattr(
            feedback,
            "is_passed"
        ):

            return (
                1.0
                if feedback.is_passed
                else 0.0
            )



        if isinstance(
            feedback,
            dict
        ):

            values = feedback.values()


        elif hasattr(
            feedback,
            "__dict__"
        ):

            values = feedback.__dict__.values()


        else:

            return 0.0



        numeric_values = [

            value

            for value in values

            if isinstance(
                value,
                (
                    int,
                    float,
                    bool
                )
            )

        ]


        if not numeric_values:

            return 0.0



        return (
            sum(numeric_values)
            /
            len(numeric_values)
        )




    async def evaluate(
        self,
        node: LATSNode
    ):
        """
        Execute node and evaluate using environment feedback.
        """


        result = await self.execute_node(
            node
        )


        node.execution_result = result



        feedback = await self.environment.evaluate(

            candidate=str(result),

            task=node.thought,

            execution_result=result,

            tool_name=node.tool

        )


        node.feedback = feedback



        node.reward = self.calculate_reward(
            feedback
        )


        node.status = "evaluated"


        # Mark as visited
        node.expanded = True


        return node




    def select_best(
        self,
        nodes
    ):
        """
        Select node with highest reward.
        """

        return max(
            nodes,
            key=lambda node: node.reward
        )




    def select_unvisited_child(
        self,
        node: LATSNode
    ):
        """
        Select unexplored branch.
        """


        for child in node.children:

            if child.status == "unvisited":

                return child


        return None




    def _available_tool_names(
        self
    ):


        registry = self.tool_registry



        if hasattr(
            registry,
            "tools"
        ):

            tools = registry.tools



        elif hasattr(
            registry,
            "registry"
        ):

            tools = registry.registry



        else:

            return []



        if isinstance(
            tools,
            dict
        ):

            return sorted(
                tools.keys()
            )



        return sorted(

            tool.name

            for tool in tools

            if hasattr(
                tool,
                "name"
            )

        )




    def backtrack(
        self,
        node: LATSNode
    ):
        """
        Return to parent node.
        """


        node.status = "failed"


        return node.parent




    async def search(
        self,
        root,
        iterations=5
    ):


        current = root



        for _ in range(iterations):


            if current is None:

                break



            children = await self.expand(
                current
            )



            if not children:

                return current



            evaluated = []



            for child in children:

                evaluated.append(

                    await self.evaluate(
                        child
                    )

                )



            best = self.select_best(
                evaluated
            )



            if best.reward >= 0.99:

                return best




            if best.reward < 1:


                parent = self.backtrack(
                    best
                )



                if parent is None:

                    break



                alternative = (
                    self.select_unvisited_child(
                        parent
                    )
                )



                if alternative:

                    current = alternative


                else:

                    current = parent



            else:

                current = best



        return current




    async def run(
        self,
        task_id: str,
        task: str
    ) -> PlannerResult:


        root = LATSNode(

            id="root",

            thought=task

        )



        best_node = await self.search(
            root
        )



        if best_node is None:

            return PlannerResult(

                success=False,

                planner=PlannerType.LATS,

                task_id=task_id,

                output="LATS failed to find a solution"

            )



        result = best_node.execution_result



        return PlannerResult(

            success=best_node.reward > 0,

            planner=PlannerType.LATS,

            task_id=task_id,

            output=str(result),

            metadata={

                "selected_node":
                    best_node.id,

                "reward":
                    best_node.reward,

                "feedback":
                    best_node.feedback

            }

        )
