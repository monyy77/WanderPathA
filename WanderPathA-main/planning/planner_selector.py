from typing import Any

from planning.schema import (
    PlannerType,
    PlannerResult
)

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


        self.ps_planner = PlanAndSolvePlanner(
            llm,
            tool_registry
        )


        self.tot_planner = TreeOfThoughtsPlanner(
            llm,
            tool_registry
        )


        self.lats_planner = LATSPlanner(
            llm,
            tool_registry,
            environment
        )



    # ==========================================
    # Planner Selection
    # ==========================================

    async def select_planner(
        self,
        task: str
    ) -> PlannerType:


        prompt = f"""

You are selecting a planning algorithm
for an airline IROPS agent.


Available planners:

1. plan_and_solve
- Simple sequential tasks
- Clear objective
- No major branching


2. tree_of_thoughts
- Multiple possible solutions
- Need compare alternatives


3. lats
- Need exploration
- Need environment feedback
- Need evaluate multiple actions



Task:

{task}



Return ONLY one word:

plan_and_solve

tree_of_thoughts

lats

"""


        response = await self.llm.ainvoke(
            prompt
        )


        choice = (
            response.content
            .strip()
            .lower()
        )


        # normalize LLM output

        choice = (
            choice
            .replace(
                "-",
                "_"
            )
            .replace(
                " ",
                "_"
            )
        )



        if "tree" in choice:

            return PlannerType.TREE_OF_THOUGHTS



        if "lats" in choice:

            return PlannerType.LATS



        if "plan" in choice:

            return PlannerType.PLAN_AND_SOLVE



        # Safe fallback

        return PlannerType.PLAN_AND_SOLVE





    # ==========================================
    # Execute Selected Planner
    # ==========================================

    async def execute_planned_task(
        self,
        task: Any,
        outputs: dict[str,str],
        goal: str
    ) -> PlannerResult:



        context = "\n\n".join(

            f"OUTPUT FROM {dependency}:\n{outputs[dependency]}"

            for dependency in task.depends_on

        ) or "No prerequisite outputs."




        full_task_prompt = f"""

Overall Goal:

{goal}


Current Task:

{task.instruction}


Previous Results:

{context}



Available MCP Tools:

{self._available_tools()}


Execution rules:

- Use only available MCP tools.
- Never invent tool names.
- Always provide required arguments.

"""



        planner_type = await self.select_planner(
            full_task_prompt
        )



        # -------------------------
        # Plan and Solve
        # -------------------------

        if planner_type == PlannerType.PLAN_AND_SOLVE:


            return await self.ps_planner.run(

                task.id,

                full_task_prompt

            )



        # -------------------------
        # Tree of Thoughts
        # -------------------------

        elif planner_type == PlannerType.TREE_OF_THOUGHTS:


            return await self.tot_planner.run(

                task.id,

                full_task_prompt

            )



        # -------------------------
        # LATS
        # -------------------------

        elif planner_type == PlannerType.LATS:


            return await self.lats_planner.run(

                task.id,

                full_task_prompt

            )



        else:


            return await self.ps_planner.run(

                task.id,

                full_task_prompt

            )





    # ==========================================
    # Tool Registry Helper
    # ==========================================

    def _available_tools(
        self
    ):

        if self.tool_registry is None:

            return []


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