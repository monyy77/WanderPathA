'''
Episode
      │
      ▼
extract_fact()
      │
      ▼
rule_based_extract()
      │
      ├──────────────┐
      │              │
 Found          Not Found
      │              │
      ▼              ▼
SemanticFact     llm_extract()
                     │
                     ▼
              Structured Output
                     │
                     ▼
               SemanticFact
'''

from memory.memory_models import Episode, SemanticFact
class ConsolidationLayer:

    def __init__(
        self,
        episodic_store,
        semantic_store,
        llm=None,
    ):
        self.episodic_store = episodic_store
        self.semantic_store = semantic_store
        self.llm = llm

    def rule_based_extract(
        self,
        episode: Episode
    ):

        text = episode.content.lower()

        if "window seat" in text:
            return SemanticFact(
                predicate="seat_preference",
                value="window",
                entity_type=episode.entity_type,
                entity_id=episode.entity_id,
                confidence=1.0,
            )

        if "aisle seat" in text:
            return SemanticFact(
                predicate="seat_preference",
                value="aisle",
                entity_type=episode.entity_type,
                entity_id=episode.entity_id,
                confidence=1.0,
            )

        return None

    def llm_extract(
        self,
        episode: Episode
    ):

        if self.llm is None:
            return None

        return self.llm.extract_fact(episode)

    def extract_fact(
        self,
        episode: Episode
    ):

        fact = self.rule_based_extract(episode)

        if fact is not None:
            return fact

        return self.llm_extract(episode)
    
    def consolidate(self):
        episodes = self.episodic_store.get_unconsolidated()

        for episode in episodes:
            fact = self.extract_fact(episode)

            if fact is None:
                self.episodic_store.mark_consolidated(episode)
                continue

            existing_fact = self.semantic_store.find_fact(
                predicate=fact.predicate,
                entity_type=fact.entity_type,
                entity_id=fact.entity_id
            )

            if existing_fact is None:
                self.semantic_store.save(fact)
                self.episodic_store.mark_consolidated(episode)
                continue

            if existing_fact.value == fact.value:
                try:
                    self.episodic_store.mark_consolidated(episode)
                except Exception as e:
                    print(f"Error marking episode as consolidated: {e}")
                continue

            self.semantic_store.close_fact(existing_fact)

            fact.version = existing_fact.version + 1
            self.semantic_store.save(fact)

            self.episodic_store.mark_consolidated(episode)


'''
get_unconsolidated()

        │

        ▼

extract_fact()

        │

        ▼

find_fact()

        │

   ┌────┴─────┐

   │          │

 None      Existing

   │          │

   ▼          ▼

save()   value changed?

             │

      ┌──────┴───────┐

      │              │

     No             Yes

      │              │

      ▼              ▼

 ignore()      close_fact()

                    │

                    ▼

             save(new version)

                    │

                    ▼

        mark_consolidated()

'''
