import time

from .long_context_tests import LONG_CONTEXT_TESTS
from .context_strategies import (
    sliding_window,
    observation_masking,
    recursive_summarization,
    zone_based_pruning,
)

def count_tokens(messages):
    # Simple fixed approximation for comparing strategies consistently.
    return sum(len(str(message.content).split()) for message in messages)

def evaluate_strategy(strategy_name, messages):
    start = time.perf_counter()

    if strategy_name == "sliding_window":
        result = sliding_window(messages, 5)

    elif strategy_name == "observation_masking":
        result = observation_masking(messages)

    elif strategy_name == "recursive_summarization":
        result = recursive_summarization(messages, 5)

    elif strategy_name == "zone_based_pruning":
        result = zone_based_pruning(messages, 5)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    latency_ms = (time.perf_counter() - start) * 1000
    tokens = count_tokens(result)

    return result, tokens, latency_ms

def check_accuracy(test_name, messages):
    text = " ".join(str(message.content).lower() for message in messages)

    expected_keywords = {
        "wheelchair_requirement": ["wheelchair"],
        "budget_constraint": ["30000"],
        "passport_requirement": ["passport", "4 months"],
    }

    keywords = expected_keywords[test_name]

    return all(keyword in text for keyword in keywords)

def run_evaluation():
    strategies = [
        "sliding_window",
        "observation_masking",
        "recursive_summarization",
        "zone_based_pruning",
    ]

    print("\n=== Context Strategy Evaluation ===\n")

    for test in LONG_CONTEXT_TESTS:
        print(f"Test: {test['name']}")

        for strategy in strategies:
            # Keep the same input for every strategy.
            messages = test["conversation"]

            result, tokens, latency = evaluate_strategy(
                strategy,
                messages,
            )
            accuracy = check_accuracy(test["name"], result)

            print(
                f"{strategy:30} "
                f"accuracy={'PASS' if accuracy else 'FAIL':4} "
                f"tokens={tokens:4} "
                f"latency={latency:.3f} ms"
)

        print()
def check_accuracy(test_name, messages):
    text = " ".join(
        str(message.content).lower()
        for message in messages
    )

    expected_keywords = {
        "wheelchair_requirement": ["wheelchair"],
        "budget_constraint": ["30000"],
        "passport_requirement": ["passport", "4 months"],
    }

    keywords = expected_keywords[test_name]

    return all(keyword in text for keyword in keywords)

if __name__ == "__main__":
    run_evaluation()
