"""Short-term memory: a rolling message buffer + a scratchpad + a queue
of MemoryItems for PromoteOrDropRouter.

Three deliberately separate structures on one object:

- ``messages`` is the rolling transcript buffer. Any of the
  context-window strategies in ``Context_eval/context_strategies.py`` are
  free to slice, mask, or summarize this list.
- ``scratchpad`` is the agent's working state: its current plan,
  sub-goal, and any high-stakes facts the customer has stated. Nothing
  in the pruning path is allowed to touch this — it's injected into the
  prompt as its own SystemMessage *after* pruning/masking runs (see
  agent.py), so it can never be cut, summarized away, or masked.
- ``items`` is the queue PromoteOrDropRouter (memory/router.py) reads
  from and removes from once it's decided forget vs. promote-to-episodic
  for an item. It never touches the transcript or the scratchpad.
"""

from langchain_core.messages import BaseMessage

from memory.memory_models import MemoryItem
from memory.scratchpad import Scratchpad


class ShortTermMemory:
    def __init__(self):
        self.messages: list[BaseMessage] = []
        self.scratchpad = Scratchpad()
        self.items: list[MemoryItem] = []

    # -- rolling message buffer ------------------------------------------------
    def add(self, message: BaseMessage):
        self.messages.append(message)

    def get_messages(self) -> list[BaseMessage]:
        return list(self.messages)

    # -- scratchpad --------------------------------------------------------
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

    def render_scratchpad_for_prompt(self) -> str:
        """Render the scratchpad as prompt text. Called fresh every agent
        step and appended after context pruning/masking, so its content
        always reflects the latest state regardless of what happened to
        the rolling buffer.
        """
        lines = ["SCRATCHPAD (do not lose this state — it is never pruned):"]

        lines.append(f"- Plan: {self.scratchpad.plan or 'not set yet'}")
        lines.append(
            f"- Current sub-goal: {self.scratchpad.current_subgoal or 'not set yet'}"
        )

        if self.scratchpad.working_state:
            lines.append("- Working state:")
            for key, value in self.scratchpad.working_state.items():
                lines.append(f"    {key}: {value}")

        if self.scratchpad.pinned_facts:
            lines.append("- Pinned customer facts (must be honored):")
            for pf in self.scratchpad.pinned_facts:
                lines.append(f"    (turn {pf.turn}, {pf.source}) {pf.fact}")
        else:
            lines.append("- Pinned customer facts: none yet")

        return "\n".join(lines)

    # -- MemoryItem queue (for PromoteOrDropRouter) -------------------------
    def add_item(self, item: MemoryItem) -> None:
        self.items.append(item)

    def get_items(self) -> list[MemoryItem]:
        return list(self.items)

    def remove(self, item: MemoryItem) -> None:
        """Required by PromoteOrDropRouter: called on both DROP (forget)
        and after a successful PROMOTE (the item now lives in episodic
        memory, so it no longer belongs in short-term). Matches by id
        rather than dataclass equality, since two distinct facts pinned
        moments apart could otherwise compare unequal only by timestamp
        and that's fragile to rely on.
        """
        self.items = [i for i in self.items if i.id != item.id]
