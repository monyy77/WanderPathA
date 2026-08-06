import time

from .long_context_tests import LONG_CONTEXT_TESTS
from .context_strategies import (
    sliding_window,
    observation_masking,
    recursive_summarization,
    zone_based_pruning,
)


def count_tokens(messages):
    return sum(len(str(message.content).split()) for message in messages)

STRATEGY_PARAMS = {
    "sliding_window": {"max_messages": 8},
    "observation_masking": {"keep_recent_observations": 2},
    "recursive_summarization": {"max_recent": 8, "chunk_size": 6},
    "zone_based_pruning": {
        "keep_recent_conversation": 6,
        "keep_recent_tool": 2,
        "keep_recent_reasoning": 2,
    },
}


def run_strategy(strategy_name, messages):
    params = STRATEGY_PARAMS[strategy_name]

    if strategy_name == "sliding_window":
        return sliding_window(messages, params["max_messages"])
    if strategy_name == "observation_masking":
        return observation_masking(messages, params["keep_recent_observations"])
    if strategy_name == "recursive_summarization":
        return recursive_summarization(messages, params["max_recent"], params["chunk_size"])
    if strategy_name == "zone_based_pruning":
        return zone_based_pruning(
            messages,
            params["keep_recent_conversation"],
            params["keep_recent_tool"],
            params["keep_recent_reasoning"],
        )

    raise ValueError(f"Unknown strategy: {strategy_name}")


def evaluate_strategy(strategy_name, messages):
    start = time.perf_counter()
    result = run_strategy(strategy_name, messages)
    latency_ms = (time.perf_counter() - start) * 1000

    tokens = count_tokens(result)
    return result, tokens, latency_ms


def check_accuracy(expected_keywords, messages):
    text = " ".join(str(message.content).lower() for message in messages)
    return all(keyword.lower() in text for keyword in expected_keywords)


def run_evaluation():
    strategies = [
        "sliding_window",
        "observation_masking",
        "recursive_summarization",
        "zone_based_pruning",
    ]

    totals = {s: {"pass": 0, "tokens": 0, "latency": 0.0} for s in strategies}

    print("\n=== Context Strategy Evaluation ===\n")

    for test in LONG_CONTEXT_TESTS:
        print(f"Test: {test['name']}  (input messages: {len(test['conversation'])})")

        for strategy in strategies:
            # Keep the same input for every strategy.
            messages = test["conversation"]

            result, tokens, latency = evaluate_strategy(strategy, messages)
            accuracy = check_accuracy(test["expected"], result)

            totals[strategy]["pass"] += int(accuracy)
            totals[strategy]["tokens"] += tokens
            totals[strategy]["latency"] += latency

            print(
                f"  {strategy:26} "
                f"accuracy={'PASS' if accuracy else 'FAIL':4} "
                f"tokens={tokens:4} "
                f"latency={latency:8.3f} ms"
            )

        print()

    n = len(LONG_CONTEXT_TESTS)
    print("=== Summary (avg across all tests) ===\n")
    print(f"{'Strategy':26} {'Accuracy':>10} {'Avg Tokens':>12} {'Avg Latency (ms)':>18}")
    for strategy in strategies:
        t = totals[strategy]
        print(
            f"{strategy:26} "
            f"{t['pass']}/{n:<8} "
            f"{t['tokens'] / n:12.1f} "
            f"{t['latency'] / n:18.3f}"
        )

    return totals, n


if __name__ == "__main__":
    run_evaluation()
