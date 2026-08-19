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

from typing import Any
from planning.schema import PlannerType, PlannerResult
from planning.plan_and_solve import PlanAndSolvePlanner
from planning.tree_of_thoughts import TreeOfThoughtsPlanner
from planning.lats import LATSPlanner


class PlannerSelector:


    def __init__(
        self,
        llm: Any,
        tool_registry: Any = None,
        environment: Any = None
    ):

        self.llm = llm
        self.tool_registry = tool_registry
        self.environment = environment

        self.ps_planner = PlanAndSolvePlanner(llm, tool_registry)
        self.tot_planner = TreeOfThoughtsPlanner(llm, tool_registry)
        self.lats_planner = LATSPlanner(llm, tool_registry, environment)



    async def select_planner(
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


        response = await self.llm.ainvoke(prompt)


        return PlannerType(
            response.content.strip().lower()
        )



    async def execute_planned_task(
        self,
        task: Any,
        outputs: dict[str, str],
        goal: str
    ) -> PlannerResult:
       

        context = "\n\n".join(
            f"OUTPUT FROM {dependency}:\n{outputs[dependency]}"
            for dependency in task.depends_on
        ) or "No prerequisite outputs."

        full_task_prompt = (
            f"Overall Goal: {goal}\n"
            f"Task: {task.instruction}\n"
            f"Context:\n{context}"
        )

        planner_type = await self.select_planner(full_task_prompt)

        if planner_type == PlannerType.TREE_OF_THOUGHTS:
            return await self.tot_planner.run(task.id, full_task_prompt)

        elif planner_type == PlannerType.LATS:
            return await self.lats_planner.run(task.id, full_task_prompt)

        else:
            return await self.ps_planner.run(task.id, full_task_prompt)