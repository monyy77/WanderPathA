"""
DAG construction + cycle check for the Planning Agent.

FORKED FROM: AmrSheta22/task_decomposition_and_planning
             planning_lab/models.py (Task, Plan)
Credit: this file is the toolkit's DAG layer, kept close to the original on
purpose (per the lab instructions: "don't rebuild the toolkit's search or
scheduling logic in a parallel file"). The only changes vs. upstream:

  1. Added `TaskType` + `Task.kind` / `Task.tool_name` so a DAG node can be
     one of: a direct MCP tool call, an LLM reasoning step, or a step that
     must be routed to a planning algorithm (PS / ToT / LATS) by
     `planner_router.py`. The upstream toolkit only ever produces plain
     "reasoning" nodes.
  2. Docstrings/comments pointing at where WanderPathA wires this in.

Everything else (id/goal validation, cycle detection via
`nx.is_directed_acyclic_graph`, topological_order, execution_batches,
terminal_tasks) is the toolkit's original logic, unmodified. A plan that
can deadlock is rejected here, at construction time, before any tool or LLM
call happens -- see `Plan.validate_dag`.
"""

from __future__ import annotations

from enum import Enum

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskType(str, Enum):
    """What kind of work a DAG node performs.

    - TOOL_CALL: a deterministic MCP tool invocation (e.g. get_flight_status).
      Single lookup/write, no branching, no self-reasoning needed.
    - REASONING: a plain LLM completion over the outputs of its dependencies
      (e.g. "assess priority from these facts"). No search needed.
    - PLANNED: a sub-task that genuinely benefits from a planning algorithm
      (Plan-and-Solve / Tree of Thoughts / LATS) because it has real
      branching or a real cost to a wrong answer. Routed by
      planner_router.py (Person 2's concern) -- this file only marks it.
    """

    TOOL_CALL = "tool_call"
    REASONING = "reasoning"
    PLANNED = "planned"


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    instruction: str = Field(min_length=5)
    depends_on: list[str] = Field(default_factory=list)

    # --- WanderPathA additions (not in upstream toolkit) ---
    kind: TaskType = TaskType.REASONING
    tool_name: str | None = None  # required when kind == TOOL_CALL


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str = Field(min_length=5)
    tasks: list[Task] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def validate_dag(self) -> "Plan":
        ids = [task.id for task in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("Task ids must be unique")
        known = set(ids)
        for task in self.tasks:
            missing = set(task.depends_on) - known
            if missing:
                raise ValueError(f"{task.id} has unknown dependencies: {sorted(missing)}")
            if task.id in task.depends_on:
                raise ValueError(f"{task.id} cannot depend on itself")
            if task.kind == TaskType.TOOL_CALL and not task.tool_name:
                raise ValueError(f"{task.id} is a TOOL_CALL task but has no tool_name")
        if not nx.is_directed_acyclic_graph(self.graph):
            cycle = nx.find_cycle(self.graph)
            blocked = sorted({node for edge in cycle for node in edge[:2]})
            raise ValueError(f"Cycle detected; blocked tasks: {blocked}")
        return self

    @property
    def graph(self) -> nx.DiGraph:
        """Dependency graph, edges directed dependency -> task."""
        graph = nx.DiGraph()
        graph.add_nodes_from(task.id for task in self.tasks)
        graph.add_edges_from(
            (dependency, task.id)
            for task in self.tasks
            for dependency in task.depends_on
        )
        return graph

    def topological_order(self) -> list[str]:
        return list(nx.topological_sort(self.graph))

    def execution_batches(self) -> list[list[str]]:
        """Parallel-safe batches; every dependency is in an earlier batch."""
        return [sorted(generation) for generation in nx.topological_generations(self.graph)]

    def task(self, task_id: str) -> Task:
        return next(task for task in self.tasks if task.id == task_id)

    def terminal_tasks(self) -> list[str]:
        return [node for node, degree in self.graph.out_degree if degree == 0]
