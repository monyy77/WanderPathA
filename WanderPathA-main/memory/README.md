# Memory & RAG — Task

## Overview

This task adds short-term and long-term memory to the Travel Support Agent.

```text
Conversation
    ↓
Short-Term Memory
    ↓
Promote-or-Drop Router
    ↓
Drop ───────────────→ Forget
    │
    ↓
Episodic Memory
    ↓
Consolidation
    ↓
Semantic Memory
    ↓
Future Conversations
```

## Architecture

### Short-Term Memory

Stores:

- Recent conversation messages
- Scratchpad: plan, sub-goal, working state, and pinned facts
- `MemoryItem` queue for memory routing

### Promote-or-Drop Router

Uses a hybrid strategy:

1. Rule-based classification first
2. Router LLM fallback for unknown cases

```text
MemoryItem
   ↓
Rule-based
   ├── PROMOTE → Episodic Memory
   ├── DROP → Remove
   └── Unknown → Router LLM
```

The Router LLM returns:

```text
PROMOTE / DROP + reason
```

### Episodic Memory

Stores important customer events as `Episode` objects.

Examples:

- Booking confirmed
- Booking cancelled
- Refund requested
- Customer preference

### Consolidation Layer

Processes unconsolidated episodes:

```text
Episode
   ↓
Rule-based Fact Extraction
   ↓
LLM fallback
   ↓
SemanticFact
```

Existing facts are updated using versioning when their values change.

### Semantic Memory

Stores persistent customer facts such as:

```text
seat_preference → window
meal_preference → vegetarian
```

Supports:

- Active/inactive facts
- Expiration
- Version history
- Retrieval by question

## LLM Components

The project uses separate LLM responsibilities:

| Component | Responsibility |
|---|---|
| `RouterLLM` | Decide `PROMOTE` or `DROP` |
| `FactExtractorLLM` | Extract persistent semantic facts |
| Scratchpad LLM | Detect high-stakes conversation facts |

All LLM outputs use structured Pydantic models.

## Agent Integration

The Agent initializes:

```text
ShortTermMemory
EpisodicMemory
SemanticMemory
ConsolidationLayer
RouterLLM
```

For every customer message:

```text
User Message
    ↓
MemoryItem
    ↓
Router
    ↓
Episodic Memory
    ↓
Periodic Consolidation
    ↓
Semantic Retrieval
    ↓
Agent Reasoning
```

## MemoryItem

`MemoryItem` connects customer messages to the memory pipeline.

```python
MemoryItem(
    id=...,
    content=...,
    speaker="customer",
    timestamp=...,
    importance=...,
    metadata=...
)
```

Metadata can include:

```text
entity_type
entity_id
turn
extraction_source
```

## Scratchpad

The scratchpad stores high-stakes facts that must survive context pruning.

Examples:

- Accessibility requirements
- Budget limits
- Passport constraints
- Refund preferences
- Hard booking conditions

The scratchpad is injected into the prompt after context pruning.

## Testing

Memory tests verify:

- Short-term memory storage
- Scratchpad state
- High-stakes fact extraction
- `MemoryItem` creation
- Scratchpad survival after pruning

Run:

```bash
python test_memory.py
```

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables:

```text
GROQ_API_KEY=your_api_key
```

## Main Technologies

- Python
- LangChain
- Groq / Llama 3.3 70B
- Pydantic
- MCP
- Short-Term Memory
- Episodic Memory
- Semantic Memory
- RAG / Context Retrieval
