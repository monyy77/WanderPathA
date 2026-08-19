# WanderPathA Benchmark Comparison

| Method | Success | Success Rate | Avg. LLM Calls | Avg. Tokens | Avg. Latency |
|:--|--:|--:|--:|--:|--:|
| **decomposition_first** | 3/5 | 60.0% | 0.0 | 0 | 82.90s |
| **dynamic** | 2/5 | 40.0% | 3.6 | 0 | 87.52s |
| **plan_and_solve** | 4/5 | 80.0% | 0.0 | 0 | 77.87s |
| **tree_of_thoughts** | 3/5 | 60.0% | 0.0 | 0 | 22.32s |
| **lats** | 0/5 | 0.0% | 0.0 | 0 | 11.31s |
| **lats_ungrounded** | 0/5 | 0.0% | 0.0 | 0 | 8.70s |
| **self_refine** | 4/5 | 80.0% | 2.0 | 0 | 4.39s |
| **reflexion** | 4/5 | 80.0% | 1.0 | 0 | 20.24s |