# Context Window Management Evaluation

## Test Suite

Five realistic WanderPath support transcripts (`long_context_tests.py`), each
built from actual agent-shaped messages (AIMessage thought/action steps +
HumanMessage tool observations), not synthetic filler:

1. `wheelchair_requirement` — decision stated at the very start (baseline case).
2. `budget_constraint` — decision stated at the very start.
3. `passport_requirement` — decision stated at the very start.
4. `refund_preference_buried_mid` — a multi-leg booking modification
   (WPT-4471, Cairo → Istanbul → Rome) where the customer's refund
   preference ("voucher, not cash") is stated *partway through*, then
   buried under tool noise for the remaining legs. This is the realistic
   failure mode from issue #30, not just "decision at the edges."
5. `conditional_change_threshold_buried_mid` — a 3-leg fare-comparison
   where a conditional instruction ("only change if under 50 USD") is
   stated mid-conversation and buried under two more legs of tool checks.

Each strategy runs against the exact same input for every test — same
messages in, different messages out. Accuracy is scored by whether the
test's own `expected` keywords survive in the strategy's output; token
count is a word-count approximation; latency is wall-clock per call.

All four strategies were run with a comparable "budget" (~8-10 messages
worth of full detail kept), so no strategy wins by being handed more room
than the others (see `STRATEGY_PARAMS` in `evaluate_context.py`).

---

## Results (averaged over all 5 tests)

| Strategy | Accuracy | Avg. Tokens | Avg. Latency (ms) |
|---|---:|---:|---:|
| Sliding Window | 0 / 5 | 74.4 | 0.003 |
| Observation & Tool-output Masking | 5 / 5 | 414.6 | 0.408 |
| Recursive Summarization | 5 / 5 | 450.8 | 99.554 |
| Zone-based Pruning | **5 / 5** | **268.2** | 0.520 |

Full per-test breakdown is printed by `python -m Context_eval.evaluate_context`.

---

## Selected Strategy

**Zone-based Pruning**

### Justification

- Tied for the best accuracy (5/5) — the customer's stated fact survives
  in every test, including both "buried mid-conversation" cases, because
  the zone scheme keeps a dedicated, protected window for real customer
  turns separate from agent-reasoning noise and tool output.
- Lowest token count among the three strategies that pass accuracy
  (268 avg vs. 414 for masking and 451 for summarization) — roughly 35%
  fewer tokens than masking for the same accuracy, because it prunes
  *three* independent zones (tool output, agent reasoning, and old
  conversation turns) instead of only tool output.
- Latency is negligible and doesn't depend on an external model call,
  unlike recursive summarization, which pays real LLM latency (or a
  network-failure delay when the model is unreachable, ~100-600ms in
  this environment) on every chunk it folds in — a real cost difference,
  not just points on a chart, when scaled to production traffic.
- Sliding window is cheapest and fastest by far but fails every accuracy
  test (0/5): it has no concept of which message matters, so it happily
  drops the customer's original statement the moment the transcript
  outgrows its window. Not viable on its own for this use case.

### A caveat worth stating plainly

Zone-based pruning only wins here because its zone classification
correctly separates customer dialogue from agent-internal reasoning and
tool noise. An earlier version of this implementation lumped agent
Thought/Action messages in with real customer turns, which let dozens of
reasoning steps crowd the customer's original statement out of the
"recent conversation" window — that version failed 0/5, the same as
sliding window. The strategy is only as good as the zone boundaries; get
the classification wrong and it degrades to sliding window with extra
steps.

### What we'd ship

Zone-based pruning for the rolling transcript, with the scratchpad
(separate from all of this — see `memory/scratchpad.py`) always injected
after pruning runs, so the customer's pinned facts are never at the mercy
of whichever strategy is active.
