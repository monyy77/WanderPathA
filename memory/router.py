from enum import Enum
from memory.memory_models import MemoryItem, Episode

class Decision(Enum):
    PROMOTE = "PROMOTE"
    DROP = "DROP"

GREETINGS = ["hello", "hi", "hey",
            "goodbye", "bye", "thanks", "thank you"]

PREFERENCES = ["prefer", "preference",
               "window seat", "aisle seat",
               "vegetarian", "vegan"]

BOOKING_EVENTS = ["booking created", "booking confirmed", "reservation confirmed"]

REFUND_EVENTS = ["refund requested", "refund approved", "refund"]

CANCELLATION_EVENTS = ["booking cancelled","booking canceled","cancel reservation"]

PROFILE_UPDATE_EVENTS = ["profile updated", "profile changed", "update profile"]

class PromoteOrDropRouter:

    def __init__(self,episodic_store,short_term,llm=None,logger=None):
        self.episodic_store = episodic_store
        self.short_term = short_term
        self.llm = llm
        self.logger = logger

    def route(self, item: MemoryItem):
        decision, reason = self.decide(item)

        if self.logger:
            self.logger.log(
                item=item,
                decision=decision,
                reason=reason
            )
        else:
            print(
                f"[Router] "
                f"{item.content} -> {decision.value} "
                f"({reason})"
            )

        if decision == Decision.PROMOTE:
            self.promote_to_episode(item, reason)
        elif decision == Decision.DROP:
            self.short_term.remove(item)
        

    def decide(self, item: MemoryItem):
        decision, reason = self.rule_based(item)
        if decision is not None:
            return decision, reason
        else:
            return self.llm_decision(item)


    def rule_based(self, item: MemoryItem):
        decision = None
        reason = None
        content = item.content.lower()

        # Greeting / Farewell
        if any(word in content for word in GREETINGS):
            decision = Decision.DROP
            reason = "Temporary conversation"

        # Customer preference
        elif any(word in content for word in PREFERENCES):
            decision = Decision.PROMOTE
            reason = "Long-term preference"

        # Booking creation
        elif any(word in content for word in BOOKING_EVENTS):
            decision = Decision.PROMOTE
            reason = "Important business event"

        # Booking cancellation
        elif any(word in content for word in CANCELLATION_EVENTS):
            decision = Decision.PROMOTE
            reason = "Important business event"

        # Refund
        elif any(word in content for word in REFUND_EVENTS):
            decision = Decision.PROMOTE
            reason = "Important business event"

        # Customer profile update
        elif any(word in content for word in PROFILE_UPDATE_EVENTS):
            decision = Decision.PROMOTE
            reason = "Persistent customer information"

        return decision, reason

    def llm_decision(self, item: MemoryItem):

        if self.llm is not None:
            return self.llm.make_decision(item)

        return (
            Decision.DROP,
            "No LLM available"
        )
    #use this function to build an episode from a memory item
    def build_episode(
        self,
        item: MemoryItem,
        reason: str
    ):

        episode = Episode(
            content=item.content,
            entity_type=item.metadata.get("entity_type", "customer"),
            entity_id=item.metadata.get("entity_id", None),
            source=item.speaker,
            reason=reason,
            metadata=item.metadata.copy()
        )

        episode.created_at = item.timestamp

        return episode

    def promote_to_episode(
        self,
        item: MemoryItem,
        reason: str
    ):

        episode = self.build_episode(item, reason)

        self.episodic_store.save(episode)

        self.short_term.remove(item)


'''

MemoryItem
      │
      ▼
decide(item)
      │
      ▼
Decision + Reason
      │
      ▼
promote(item, reason)
      │
      ▼
Episode(reason=reason)
      │
      ▼
episodic_store.save()

'''


'''
Short-term Memory
        │
        ▼
 old_items
        │
        ▼
PromoteOrDropRouter
        │
        ├─────────────┐
        │             │
        ▼             ▼
     DROP         PROMOTE
        │             │
        ▼             ▼
 remove()      build_episode()
                      │
                      ▼
              episodic_store.save()
                      │
                      ▼
           Consolidation Layer
                      │
                      ▼
          Semantic Memory (Facts)
'''
