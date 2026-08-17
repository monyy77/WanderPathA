'''
User
 |
Agent
 |
Planner Selector
 |
 -------------------------
 |           |            |
PlanSolve   ToT          LATS
 |
MCP Tool Registry
 |
MCP Server
 |
Database

'''

from planning.schema import PlannerType


class PlannerSelector:


    def __init__(self, llm):

        self.llm = llm



    def select_planner(
        self,
        task: str
    ) -> PlannerType:


        prompt = f"""

        Select the best planner.

        Options:

        plan_and_solve
        tree_of_thoughts
        lats


        Rules:

        Simple task:
        plan_and_solve


        Multiple alternatives:
        tree_of_thoughts


        Optimization with environment feedback:
        lats


        Task:

        {task}


        Return only planner name.

        """


        response = self.llm.invoke(prompt)


        return PlannerType(
            response.content.strip().lower()
        )
