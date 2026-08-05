from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import BaseMessage 

@dataclass
class Scratchpad:
    plan: str | None = None
    current_subgoal: str | None = None
    working_state: dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    def __init__(self):
        self.messages: list[BaseMessage] = []
        self.scratchpad = Scratchpad()

    def add(self, message: BaseMessage):
        self.messages.append(message)

    def get_messages(self) -> list[BaseMessage]:
        return list(self.messages)

    def update_scratchpad(
        self,
        plan: str | None = None,
        current_subgoal: str | None = None,
        **working_state,
    ):
        if plan is not None:
            self.scratchpad.plan = plan

        if current_subgoal is not None:
            self.scratchpad.current_subgoal = current_subgoal

        self.scratchpad.working_state.update(working_state)

    def get_scratchpad(self) -> Scratchpad:
        return self.scratchpad
