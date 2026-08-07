from datetime import datetime

from memory.memory_models import SemanticFact


class SemanticMemory:

    def __init__(self):
        self.facts: list[SemanticFact] = []

    def save(self, fact: SemanticFact):
        self.facts.append(fact)

    def find_fact(
        self,
        predicate: str,
        entity_type: str,
        entity_id: int,
    ) -> SemanticFact | None:

        for fact in self.facts:
            if (
                fact.predicate == predicate
                and fact.entity_type == entity_type
                and fact.entity_id == entity_id
                and fact.valid_until is None
            ):
                return fact

        return None

    def close_fact(self, fact: SemanticFact):
        fact.valid_until = datetime.now()

    def get_fact_history(
        self,
        entity_type: str,
        entity_id: int,
        predicate: str,
    ) -> list[SemanticFact]:

        return [
            fact
            for fact in self.facts
            if (
                fact.entity_type == entity_type
                and fact.entity_id == entity_id
                and fact.predicate == predicate
            )
        ]

    def get_all(self) -> list[SemanticFact]:
        return list(self.facts)

    def is_expired(
        self,
        fact: SemanticFact
    ):
        if fact.expires_at is None:
            return False

        return fact.expires_at <= datetime.now()

    def get_entity_facts(
        self,
        entity_type: str,
        entity_id: str | None
    ) -> list[SemanticFact]:
        return [
            fact
            for fact in self.facts
            if (
                fact.entity_type == entity_type
                and fact.entity_id == entity_id
                and fact.valid_until is None
                and not self.is_expired(fact)
            )
        ]

    def get_active_facts(self):
        return [
            fact
            for fact in self.facts
            if (
                fact.valid_until is None
                and not self.is_expired(fact)
            )
        ]

    def retrieve(
        self,
        question: str
    ) -> list[SemanticFact]:
        """
        Return semantic facts relevant to the question.
        Only active (non-expired) facts are returned.
        """
        keywords = question.lower().split()

        return [
            fact
            for fact in self.get_active_facts()
            if any(
                word in (
                    f"{fact.predicate} {fact.value}"
                ).lower()
                for word in keywords
            )
        ]
