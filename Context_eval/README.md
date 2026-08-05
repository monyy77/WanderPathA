# Context Evaluation

This module implements short-term memory and context window management strategies for the constrained travel support agent.

## Files

- `memory.py` – Short-term memory and scratchpad implementation.
- `context_strategies.py` – Context window management strategies:
  - Sliding Window
  - Observation Masking
  - Recursive Summarization
  - Zone-Based Pruning
- `test_memory.py` – Unit tests for memory and scratchpad.
- `test_strategies.py` – Tests for all context strategies.
- `long_context_tests.py` – Long conversation evaluation scenarios.
- `evaluate_context.py` – Compares strategies by accuracy, token usage, and latency.
- `comparison_results.md` – Evaluation results.

## Running

Run the memory tests:

```bash
python -m Context_eval.test_memory
```

Run the strategy tests:

```bash
python -m Context_eval.test_strategies
```

Run the evaluation:

```bash
python -m Context_eval.evaluate_context
```
