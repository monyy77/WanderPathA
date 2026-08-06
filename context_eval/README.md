### Context Evaluation

This module implements context window management strategies for the constrained travel support agent, and evaluates them against realistic long, tool-heavy WanderPath support transcripts.

Short-term memory and the scratchpad live in the separate top-level memory/ package, not here — see memory/README.md. This module only prunes the rolling message buffer; it never touches the scratchpad.

### Files
context_strategies.py – The four context window management strategies:
Sliding Window
Observation & Tool-output Masking
Recursive Summarization
Zone-Based Pruning
test_strategies.py – Unit tests for all four strategies.
long_context_tests.py – Long-conversation evaluation scenarios (5 realistic multi-step WanderPath transcripts, including cases where the key customer fact is buried mid-conversation, not just at the edges).
evaluate_context.py – Runs all four strategies against the same test suite and compares them by accuracy, token usage, and latency.
comparison_results.md – Evaluation results and the strategy selected for the agent (zone_based_pruning, currently wired into agent/agent.py).
### Running

Run the strategy unit tests:
python -m Context_eval.test_strategies

Run the full evaluation (prints per-test and summary results):
python -m Context_eval.evaluate_context

For the memory/scratchpad tests, see memory/README.md.
