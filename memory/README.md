Overview

This task implements a multi-layer memory system for a travel-support Agent:

User Message
     ↓
Short-Term Memory
     ↓
Promote-or-Drop Router
     ├── DROP
     └── PROMOTE
            ↓
      Episodic Memory
            ↓
     Consolidation Layer
            ↓
      Semantic Memory
            ↓
   Future Conversations
Memory Layers
Short-Term Memory

Stores:

Recent conversation messages
Scratchpad: plan, sub-goals, working state, and pinned facts
MemoryItem queue for the memory router

The transcript can be pruned without losing the scratchpad.

Promote-or-Drop Router

Uses a hybrid approach:

Rule-based classification for known patterns.
RouterLLM fallback for unknown cases.
MemoryItem
    ↓
Rule-based
 ┌──┴──┐
Found  Not Found
 ↓        ↓
Decision RouterLLM

The Router decides:

PROMOTE → save as an Episode
DROP → remove from short-term memory
Episodic Memory

Stores important customer events and promoted memories that may be useful later.

Consolidation

Processes unconsolidated episodes:

Episode
   ↓
Rule-based extraction
   ↓
LLM fallback
   ↓
SemanticFact

It also handles fact updates by closing the old fact and creating a new version.

Semantic Memory

Stores persistent facts such as:

seat_preference → window

Facts support:

Versioning
Expiration
History
Entity-based retrieval
Question-based retrieval
LLM Components

The project separates LLM responsibilities:

RouterLLM

Answers:

Should this memory be kept?

Returns:

PROMOTE / DROP + reason
FactExtractorLLM

Answers:

What persistent fact does this episode contain?

Returns:

predicate
value
confidence

Both use structured output with Pydantic.

Agent Integration

The Agent initializes one memory system per customer and connects:

Agent
 ↓
ShortTermMemory
 ↓
MemoryItemFactory
 ↓
PromoteOrDropRouter
 ↓
EpisodicMemory
 ↓
ConsolidationLayer
 ↓
SemanticMemory

Semantic facts are retrieved and injected into the Agent context during future turns.

High-Stakes Scratchpad

Customer constraints such as:

Accessibility requirements
Budget limits
Passport constraints
Refund preferences

are detected using rules first, LLM fallback second.

They are stored both as:

PinnedFact → preserved in the scratchpad
MemoryItem → processed by the Router
Testing

The memory tests verify:

Short-term memory storage
Scratchpad state
High-stakes fact detection
MemoryItem creation
Scratchpad survival after context pruning
Main Components
memory/
├── memory_models.py
├── short_term_memory.py
├── scratchpad.py
├── memory_item_factory.py
├── router.py
├── episodic_memory.py
├── consolidation.py
├── fact_extractor_llm.py
└── semantic_memory.py

The system provides short-term, episodic, and semantic memory, with rule-based + LLM decision making and full integration into the Agent workflow.
