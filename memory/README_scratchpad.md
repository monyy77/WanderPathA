### Memory
Short-term memory for the travel support agent: a rolling message buffer and a scratchpad, kept as two deliberately separate structures so that pruning the transcript (see Context_eval/) can never destroy the agent's active plan, sub-goal, or the high-stakes facts a customer has stated.
### Files
scratchpad.py –
ShortTermMemory – the rolling message buffer + the scratchpad.
Scratchpad / PinnedFact – the scratchpad's data model: plan, current sub-goal, working state, and pinned customer facts.
process_customer_message() – detects and pins high-stakes facts from a customer message (accessibility needs, budget limits, passport validity, refund preference, conditional instructions). Rule-based first; falls back to an LLM call only when no rule fires.
test_memory.py – Unit tests covering the scratchpad, fact pinning, and — most importantly — that the scratchpad survives aggressive transcript pruning untouched.
### Running
python -m memory.test_memory
