import time


def measure_latency(function, *args, **kwargs):
    """
    Measure execution time of any function.

    Returns:
        result: Function output
        latency: Execution time in seconds
    """

    start = time.perf_counter()

    result = function(*args, **kwargs)

    end = time.perf_counter()

    latency = end - start

    return result, round(latency, 3)


def evaluate_accuracy(expected, predicted):
    """
    Simple accuracy check.

    Returns:
        Correct / Incorrect
    """

    expected = expected.lower().strip()
    predicted = predicted.lower().strip()

    if expected in predicted:
        return "Correct"

    return "Incorrect"


def estimate_tokens(text):
    """
    Rough token estimation.

    (≈ 1 token = 4 characters)
    """

    return max(1, len(text) // 4)


def count_total_tokens(question, answer):
    """
    Estimate total prompt + answer tokens.
    """

    return (
        estimate_tokens(question)
        + estimate_tokens(answer)
    )