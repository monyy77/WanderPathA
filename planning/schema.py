from enum import Enum
from typing import Any

from dataclasses import dataclass, field

from pydantic import BaseModel, Field


class PlannerType(str, Enum):

    PLAN_AND_SOLVE = "plan_and_solve"

    TREE_OF_THOUGHTS = "tree_of_thoughts"

    LATS = "lats"



class EnvironmentFeedback(BaseModel):
    """
    Grounded feedback produced by the external environment.

    This object is intentionally independent from LLM reasoning.
    """

    success: bool

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    details: list[str] = Field(
        default_factory=list
    )



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


    feedback: EnvironmentFeedback | None = None


    expanded: bool = False


    execution_result: Any = None



class PlannerResult(BaseModel):

    success: bool

    planner: PlannerType

    task_id: str

    output: str


    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list
    )


    metadata: dict[str, Any] = Field(
        default_factory=dict
    )
