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



    def available_tools(self):

        """
        Return real MCP tools only.
        Prevent hallucinated tools.
        """

        if hasattr(
            self.tool_registry,
            "tools"
        ):
            return list(
                self.tool_registry.tools.keys()
            )


        if hasattr(
            self.tool_registry,
            "registry"
        ):
            return list(
                self.tool_registry.registry.keys()
            )


        return []



    async def expand(
        self,
        node: LATSNode
    ):

        tools = self.available_tools()


        prompt = f"""

You are a LATS planner for an airline IROPS agent.

Current state:

{node.thought}


Available MCP tools:

{tools}


Generate exactly 3 possible next actions.


STRICT RULES:

1. Tool name MUST be one of the available tools above.
2. Never invent tools.
3. If no tool is required, use:
   "tool": null
4. Arguments must match the tool requirements.
5. Return ONLY JSON.


Example:

[
 {{
   "description":"Get customer profile",
   "tool":"get_customer_profile",
   "args":
   {{
      "user_id":"C002"
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


        except Exception:

            responses = []



        children = []


        for i,item in enumerate(responses):


            tool = item.get(
                "tool"
            )


            args = item.get(
                "args",
                {}
            )


            # ===============================
            # Tool validation
            # ===============================

            if tool:

                if tool not in tools:
                    continue


                if not args:
                    continue



            child = LATSNode(

                id=f"{node.id}-{i}",

                thought=item.get(
                    "description",
                    ""
                ),

                parent=node,

                tool=tool,

                args=args

            )


            children.append(
                child
            )


            node.children.append(
                child
            )



        node.expanded=True


        return children





    async def execute_node(
        self,
        node:LATSNode
    ):


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

            values = [
                v
                for v in feedback.values()
                if isinstance(
                    v,
                    (int,float,bool)
                )
            ]

            if values:

                return sum(values)/len(values)



        return 0.0





    async def evaluate(
        self,
        node:LATSNode
    ):


        result = await self.execute_node(
            node
        )


        node.execution_result=result



        feedback = await self.environment.evaluate(

            candidate=str(result),

            task=node.thought,

            execution_result=result,

            tool_name=node.tool,

        )



        node.feedback=feedback



        node.reward=self.calculate_reward(
            feedback
        )


        node.status="evaluated"



        return node





    def select_best(
        self,
        nodes
    ):


        return max(
            nodes,
            key=lambda x:x.reward
        )





    def select_unvisited_child(
        self,
        node
    ):


        for child in node.children:

            if not child.expanded:

                return child


        return None





    def backtrack(
        self,
        node
    ):


        node.status="failed"

        return node.parent





    async def search(
        self,
        root,
        iterations=5
    ):


        current=root


        for _ in range(iterations):


            if current is None:
                break



            children = await self.expand(
                current
            )


            if not children:

                return current



            evaluated=[]



            for child in children:

                evaluated.append(
                    await self.evaluate(child)
                )



            best=self.select_best(
                evaluated
            )



            if best.reward==1:

                return best



            parent=self.backtrack(
                best
            )


            if parent is None:
                break



            alternative=self.select_unvisited_child(
                parent
            )


            current = (
                alternative
                if alternative
                else parent
            )



        return current





    async def run(
        self,
        task_id:str,
        task:str
    ) -> PlannerResult:


        root=LATSNode(

            id="root",

            thought=task

        )



        best_node=await self.search(
            root
        )



        result=best_node.execution_result



        return PlannerResult(

            success=best_node.reward>0,

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