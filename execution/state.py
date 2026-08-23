from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskState:

    tool_name: str

    input: dict

    status: str = "pending"

    result: Any = None

    error: str | None = None


@dataclass
class ExecutionState:

    tasks: list[TaskState]

    current_step: int = 0

    completed: bool = False
