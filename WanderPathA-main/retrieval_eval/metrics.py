import time
from dotenv import load_dotenv

load_dotenv()

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


from langchain_groq import ChatGroq

judge = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

def evaluate_accuracy(question, expected, answer):
    prompt = f"""
You are evaluating a Retrieval-Augmented Generation (RAG) system.

Question:
{question}

Expected Answer:
{expected}

Generated Answer:
{answer}

Determine whether the generated answer correctly answers the question based on the expected answer.

Ignore:
- Different wording
- Extra correct details
- Different sentence order
- Bullet points instead of paragraphs

Only check whether the generated answer is factually correct and contains the important information from the expected answer.

Reply with ONLY one word:
Correct
or
Incorrect
"""

    result = judge.invoke(prompt).content.strip().upper()

    if "CORRECT" in result:
        return "Correct"
    else:
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