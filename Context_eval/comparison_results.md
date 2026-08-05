# Context Window Management Evaluation

## Test Suite

The same fixed long-context test suite was used for all strategies.

Scenarios:
1. Wheelchair accessibility requirement
2. Budget constraint
3. Passport expiry requirement

---

## Results

| Strategy | Accuracy | Avg. Tokens | Avg. Latency (ms) |
|----------|----------|------------:|------------------:|
| Sliding Window | 0 / 3 | 113 | 0.003 |
| Observation & Tool-output Masking | 3 / 3 | 102 | 0.674 |
| Recursive Summarization | 3 / 3 | 673 | 0.097 |
| Zone-based Pruning | 0 / 3 | 113 | 0.012 |

---

## Selected Strategy

Observation & Tool-output Masking

### Justification

- Preserved all important customer information.
- Achieved 100% task accuracy.
- Consumed significantly fewer tokens than recursive summarization.
- Better suited for long, tool-heavy customer support conversations in WanderPath.
