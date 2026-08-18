from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from dataclasses import dataclass

from dataclasses import dataclass, field
from typing import Any

@dataclass
class ThoughtNode:
    id: str
    description: str
    tool: str | None
    args: dict
    score: float = 0.0


@dataclass
class LATSNode:
    id: str
    thought: str

    parent: "LATSNode | None" = None

    children: list["LATSNode"] = field(
        default_factory=list
    )

    tool: str | None = None

    args: dict[str, Any] = field(
        default_factory=dict
    )

    reward: float = 0.0

    status: str = "unvisited"

    feedback: dict[str, Any] = field(
        default_factory=dict
    )

class PlannerType(str, Enum):
    PLAN_AND_SOLVE = "plan_and_solve"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    LATS = "lats"


class PlannerResult(BaseModel):
    success: bool
    planner: PlannerType
    task_id: str
    output: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
