# Short-Term Memory & Scratchpad

This covers the short-term memory component of the `memory/` package.
Long-term memory (episodic memory, semantic memory, consolidation, and
the promote-or-drop routing between them) is a separate component,
documented separately by the teammate who owns it.

Two structures are kept deliberately separate so that pruning the
transcript never destroys the agent's active plan:

- **The rolling message buffer** (`ShortTermMemory.messages`) — the raw
  conversation. Free to be sliced, masked, or summarized by the context
  window strategies in `Context_eval/`.
- **The scratchpad** (`ShortTermMemory.scratchpad`) — the agent's
  working state (plan, current sub-goal, pinned high-stakes facts).
  Never pruned. Injected into the prompt fresh every step (see
  `agent/agent.py`), after pruning runs, so it can't be cut, summarized
  away, or masked.

## Files (split by responsibility)

- **`scratchpad.py`** — just the data model: `Scratchpad` and
  `PinnedFact`. No logic, no imports beyond the standard library.

- **`short_term_memory.py`** — the `ShortTermMemory` container. Holds
  the message buffer, the scratchpad, *and* `items`: a queue of
  `MemoryItem` objects (defined in `memory_models.py`, owned by the
  teammate working on long-term memory) waiting for the
  promote-or-drop router to decide forget-vs-promote on. Provides
  `add_item()`, `get_items()`, and `remove(item)` — `remove()`
  specifically exists because the router calls
  `self.short_term.remove(item)` directly once it's made a decision.

- **`fact_extraction.py`** — the logic that decides *what counts as
  worth remembering*. `process_customer_message()` runs a set of rules
  first (accessibility needs, budget limits, passport validity, refund
  preference, conditional instructions — fast, free, deterministic),
  and only falls back to an LLM call when no rule matches. For every
  fact found, it does two things: pins it to the scratchpad (so the
  agent itself never loses it) and builds a `MemoryItem` via
  `_make_memory_item()`, which it hands to
  `short_term_memory.add_item()` — this is the item the promote-or-drop
  router later reads and routes.

- **`test_memory.py`** — unit tests covering the scratchpad, fact
  pinning into both the scratchpad and the `MemoryItem` queue, and —
  most importantly — that the scratchpad survives aggressive transcript
  pruning untouched.

## How this hands off to long-term memory

```
fact_extraction.py            short_term_memory.py             router.py
       │                             │                              │
"wheelchair" detected     stores the MemoryItem in                  │
       │                    self.items                              │
       └──► add_item() ───────────► [items] ◄──── get_items() ──────┘
                                        │
                                        └──────► remove() ◄──── route()
```

This component's job stops at "this fact is worth remembering, here's a
`MemoryItem` for it." Whether that item is later forgotten or promoted
to episodic memory is decided entirely by the routing component —
`fact_extraction.py` and the router never import or call each other
directly; they only meet through `short_term_memory.items`.

## Running
python -m memory.test_memory
