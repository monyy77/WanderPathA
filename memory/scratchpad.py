import re
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import BaseMessage


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


_RULES: list[tuple[re.Pattern, str | None]] = [
    (
        re.compile(r"wheelchair|accessib\w*|mobility[- ]impair\w*", re.I),
        "Customer requires wheelchair/accessibility accommodation.",
    ),
    (
        re.compile(
            r"(?:budget|maximum|max)[^.\n]{0,20}?(\d[\d,]{2,})\s*(egp|usd|\$|le)?",
            re.I,
        ),
        None,  # dynamic fact text built from the match, see below
    ),
    (
        re.compile(
            r"passport[^.\n]{0,40}?(expir\w*)[^.\n]{0,20}?(\d+\s*(?:month|week|day)s?)",
            re.I,
        ),
        None,
    ),
    (
        re.compile(r"voucher\b", re.I),
        "Customer prefers refund as a travel voucher, not cash.",
    ),
    (
        re.compile(r"\bcash\b.{0,15}refund|refund.{0,15}\bcash\b", re.I),
        "Customer prefers refund as cash, not a voucher.",
    ),
    (
        re.compile(
            r"only\s+(?:change|update|modify|rebook)[^.\n]{0,60}",
            re.I,
        ),
        None,
    ),
]


def _extract_rule_facts(text: str) -> list[str]:
    facts: list[str] = []

    for pattern, static_fact in _RULES:
        match = pattern.search(text)
        if not match:
            continue

        if static_fact is not None:
            facts.append(static_fact)
            continue

        # Dynamic facts: build a readable sentence from what was matched
        # instead of storing the raw regex groups.
        if "budget" in pattern.pattern or "maximum" in pattern.pattern:
            amount = match.group(1)
            currency = match.group(2) or ""
            facts.append(f"Customer's maximum budget is {amount} {currency}".strip() + ".")
        elif "passport" in pattern.pattern:
            duration = match.group(2)
            facts.append(f"Customer's passport expires in {duration}.")
        elif pattern.pattern.startswith("only"):
            facts.append(f"Conditional instruction from customer: \"{match.group(0).strip()}\"")

    return facts


def _extract_llm_fact(user_input: str) -> str | None:
    """LLM fallback: only called when no rule matched. Best-effort — if the
    model/API isn't available, this quietly returns None rather than
    breaking the agent turn.
    """
    try:
        from langchain.chat_models import init_chat_model
        from pydantic import BaseModel

        class FactExtraction(BaseModel):
            has_high_stakes_fact: bool
            fact: str = ""

        model = init_chat_model(
            model="llama-3.3-70b-versatile",
            model_provider="groq",
            max_tokens=128,
            max_retries=1,
        ).with_structured_output(FactExtraction)

        result = model.invoke(
            [
                (
                    "system",
                    "You extract high-stakes facts from a travel customer's "
                    "message that a support agent must remember for the rest "
                    "of the conversation (accessibility needs, budget limits, "
                    "document/passport constraints, refund/payment "
                    "preferences, hard conditions on changes). If the message "
                    "has no such fact, set has_high_stakes_fact to false. "
                    "Keep the fact to one short sentence.",
                ),
                ("user", user_input),
            ]
        )

        if result.has_high_stakes_fact and result.fact.strip():
            return result.fact.strip()
        return None
    except Exception:
        return None


def process_customer_message(memory: ShortTermMemory, user_input: str, turn: int) -> None:
    """Detect and pin any high-stakes fact in this customer message.

    Rules run first; the LLM fallback only runs if the rules find nothing,
    so a normal turn ("yes that's fine", "ok thanks") never costs a model
    call.
    """
    rule_facts = _extract_rule_facts(user_input)

    if rule_facts:
        for fact in rule_facts:
            memory.scratchpad.pin(fact, turn=turn, source="rule")
        return

    llm_fact = _extract_llm_fact(user_input)
    if llm_fact:
        memory.scratchpad.pin(llm_fact, turn=turn, source="llm")
