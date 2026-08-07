import pandas as pd

from langchain_groq import ChatGroq

from questions import questions
from metrics import measure_latency

from rag.naive_rag import naive_rag
from rag.hybrid_rag import hybrid_rag
from rag.agentic_rag import agentic_rag


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

    if result == "CORRECT":
        return "Correct"
    else:
        return "Incorrect"

architectures = [
    ("Naive RAG", naive_rag),
    ("Hybrid RAG", hybrid_rag),
    ("Agentic RAG", agentic_rag)
]


rows = []

for item in questions:

    question = item["question"]
    expected = item["expected"]

    for architecture_name, rag_function in architectures:

        answer, latency = measure_latency(
            rag_function,
            question
        )

        accuracy = evaluate_accuracy(
            question,
            expected,
            answer
        )

        estimated_tokens = len(answer.split())

        rows.append({

            "Architecture": architecture_name,

            "Question": question,

            "Expected": expected,

            "Answer": answer,

            "Accuracy": accuracy,

            "Latency (s)": round(latency, 3),

            "Estimated Tokens": estimated_tokens

        })


df = pd.DataFrame(rows)

print("\n================ FINAL COMPARISON ================\n")

print(df)

df.to_csv(
    "results.csv",
    index=False
)

print("\nResults saved to retrieval_eval/results.csv")