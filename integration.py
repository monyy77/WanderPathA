import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).resolve().parent.parent))

from retrieval_eval.questions import questions
from retrieval_eval.metrics import (
    measure_latency,
    evaluate_accuracy,  # ستعمل الآن بنظام LLM Judge المستورد من metrics
    count_total_tokens
)

from rag.naive_rag import naive_rag
from rag.hybrid_rag import hybrid_rag
from rag.agentic_rag import agentic_rag

ARCHITECTURES = {
    "Naive RAG": naive_rag,
    "Hybrid RAG": hybrid_rag,
    "Agentic RAG": agentic_rag
}


def evaluate():
    results = []

    for q in questions:
        question = q["question"]
        expected = q["expected"]

        print("=" * 80)
        print("Question:", question)

        for name, model in ARCHITECTURES.items():

            # 1. Measure latency
            answer, latency = measure_latency(
                model,
                question
            )

            # 2. Evaluate accuracy (تمرير البرامترات الثلاثة المطلوبة للـ LLM Judge)
            accuracy = evaluate_accuracy(
             
                expected,
                answer
            )

            # 3. Estimate tokens
            tokens = count_total_tokens(
                question,
                answer
            )

            results.append({
                "Architecture": name,
                "Question": question,
                "Expected": expected,
                "Answer": answer,
                "Accuracy": accuracy,
                "Latency (s)": round(latency, 3),
                "Estimated Tokens": tokens
            })

            print(f"\n{name}")
            print("-" * 40)
            print("Answer:")
            print(answer)
            print(f"Latency: {latency:.3f} s")
            print(f"Accuracy: {accuracy}")
            print(f"Estimated Tokens: {tokens}")

    df = pd.DataFrame(results)

    print("\n================ FINAL COMPARISON ================\n")
    print(df)

    # حفظ النتائج
    output_path = Path("retrieval_eval/results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"\nResults saved to {output_path}")

    return df


if __name__ == "__main__":
    evaluate()