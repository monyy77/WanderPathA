"""The scratchpad data model: the agent's working state, kept separate
from the rolling message buffer (see short_term_memory.py) so pruning
the transcript can never destroy it.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PinnedFact:
    """A single high-stakes fact pinned from a customer message."""

    turn: int
    fact: str
    source: str  # "rule" or "llm"


@dataclass
class Scratchpad:
    plan: str | None = None
    current_subgoal: str | None = None
    working_state: dict[str, Any] = field(default_factory=dict)
    pinned_facts: list[PinnedFact] = field(default_factory=list)

    def pin(self, fact: str, turn: int, source: str = "rule") -> None:
        # Avoid pinning the exact same fact twice (e.g. customer repeats
        # themselves, or the rule + LLM fallback both fire across turns).
        if any(existing.fact == fact for existing in self.pinned_facts):
            return
        self.pinned_facts.append(PinnedFact(turn=turn, fact=fact, source=source))
