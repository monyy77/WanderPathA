import json

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



    async def expand(
        self,
        node: LATSNode
    ):
        """
        Generate multiple possible next actions.
        Tree Expansion step.
        """

        prompt = f"""
        Current state:

        {node.thought}


        Generate 3 possible next actions.

        Return ONLY valid JSON.

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
          }},
          {{
            "description": "Choose VIP preferred flight",
            "tool": "search_flights",
            "args": {{
                "sort": "preference"
            }}
          }}
        ]

        """


        response = await self.llm.ainvoke(prompt)


        # LangChain returns AIMessage
        try:
            responses = parse_json_markdown(response.content)
            if not isinstance(responses, list):
                responses = []
        except Exception:
            responses = []


        for i, item in enumerate(responses):

            child = LATSNode(

                id=f"{node.id}-{i}",

                thought=item["description"],

                parent=node,

                tool=item.get("tool"),

                args=item.get(
                    "args",
                    {}
                )
            )


            node.children.append(
                child
            )


        # Mark node as expanded
        node.expanded = True


        return node.children



    async def execute_node(
        self,
        node: LATSNode
    ):
        """
        Execute selected action using MCP Tool Registry.
        """


        if not node.tool:
            return None


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

        if hasattr(feedback, "score"):
            return float(feedback.score)
            
        if hasattr(feedback, "is_passed"):
            return 1.0 if feedback.is_passed else 0.0

        if hasattr(feedback, "__dict__"):
            fb_dict = feedback.__dict__
        elif isinstance(feedback, dict):
            fb_dict = feedback
        else:
            return 0.0

        if not fb_dict:
            return 0.0

        numeric_values = [v for v in fb_dict.values() if isinstance(v, (int, float, bool))]
        if not numeric_values:
            return 0.0

        return sum(numeric_values) / len(numeric_values)

    
    async def evaluate(
        self,
        node: LATSNode
    ):
        """
        Execute node and evaluate using real environment feedback.
        """


        result = await self.execute_node(node)


        # Store execution result
        node.execution_result = result



        # Environment feedback
        feedback = await self.environment.evaluate(
    candidate=str(result),
    task=node.thought,
    execution_result=result,
    tool_name=node.tool,
)

        node.feedback = feedback



        # Reward based on feedback
        node.reward = self.calculate_reward(
            feedback
        )


        node.status = "evaluated"


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
            key=lambda x: x.reward
        )



    def select_unvisited_child(
        self,
        node: LATSNode
    ):
        """
        Select unexplored branch.
        """


        for child in node.children:


            if not child.expanded:

                return child



        return None



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


            # No possible branches
            if not children:
                return current



            evaluated = []



            for child in children:

                evaluated.append(
                    await self.evaluate(child)
                )



            best = self.select_best(
                evaluated
            )



            # Perfect solution found
            if best.reward == 1:

                return best



            # Need exploration/backtracking
            if best.reward < 1:


                parent = self.backtrack(
                    best
                )


                if parent is None:
                    break



                alternative = self.select_unvisited_child(
                    parent
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



        best_node = await self.search(root)



        # Use previous execution result
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
    

'''

User Task
    |
    v
Root Node
    |
Expand
    |
 ----------------
 |       |       |
 A       B       C
 |       |       |
Execute Execute Execute
 |       |       |
Environment Feedback
 |       |       |
Reward Reward Reward
        |
   Select Best
        |
   Backtrack if fail
        |
   Final Node Result

'''
