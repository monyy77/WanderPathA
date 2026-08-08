import re
import uuid
from datetime import datetime

from memory.memory_models import MemoryItem, SemanticFact
from memory.Short_term_memory import ShortTermMemory

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
        None,  # dynamic fact text built from the match
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


class FactExtractorLLM:
    """LLM extractor used by ConsolidationLayer to resolve episodic memories into semantic facts."""

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.model_name = model_name

    def extract_fact(self, episode) -> SemanticFact | None:
        try:
            from langchain.chat_models import init_chat_model
            from pydantic import BaseModel

            class ExtractedFact(BaseModel):
                has_fact: bool
                predicate: str = ""
                value: str = ""

            model = init_chat_model(
                model=self.model_name,
                model_provider="groq",
                max_tokens=128,
                max_retries=1,
            ).with_structured_output(ExtractedFact)

            content = getattr(episode, "content", str(episode))
            result = model.invoke(
                [
                    (
                        "system",
                        "Extract key persistent customer facts (e.g., seat_preference: window, max_budget: 15000 EGP) "
                        "from the episode. If no key fact exists, set has_fact to false.",
                    ),
                    ("user", content),
                ]
            )

            if result.has_fact and result.predicate and result.value:
                return SemanticFact(
                    predicate=result.predicate.strip().lower(),
                    value=result.value.strip().lower(),
                    entity_type=getattr(episode, "entity_type", "customer"),
                    entity_id=getattr(episode, "entity_id", "CUST-101"),
                    confidence=0.85,
                )
            return None
        except Exception:
            return None


def _extract_rule_facts(text: str) -> list[str]:
    facts: list[str] = []

    for pattern, static_fact in _RULES:
        match = pattern.search(text)
        if not match:
            continue

        if static_fact is not None:
            facts.append(static_fact)
            continue

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


def _make_memory_item(fact: str, turn: int, source: str) -> MemoryItem:
    return MemoryItem(
        id=str(uuid.uuid4()),
        content=fact,
        speaker="customer",
        timestamp=datetime.now(),
        importance=0.9 if source == "rule" else 0.7,
        metadata={"turn": turn, "extraction_source": source},
    )


def process_customer_message(memory: ShortTermMemory, user_input: str, turn: int) -> None:
    rule_facts = _extract_rule_facts(user_input)

    if rule_facts:
        for fact in rule_facts:
            memory.scratchpad.pin(fact, turn=turn, source="rule")
            memory.add_item(_make_memory_item(fact, turn, source="rule"))
        return

    llm_fact = _extract_llm_fact(user_input)
    if llm_fact:
        memory.scratchpad.pin(llm_fact, turn=turn, source="llm")
        memory.add_item(_make_memory_item(llm_fact, turn, source="llm"))