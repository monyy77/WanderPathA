from __future__ import annotations

import json
from pathlib import Path


METHODS = [
    "decomposition_first",
    "dynamic",
    "plan_and_solve",
    "tree_of_thoughts",
    "lats",
    "lats_ungrounded",
    "self_refine",
    "reflexion",
]


def aggregate(results):

    table = {}

    for method in METHODS:

        rows = [
            r for r in results
            if r["method"] == method
        ]

        if not rows:
            continue

        successes = sum(
            r["success"]
            for r in rows
        )

        table[method] = {
            "runs": len(rows),
            "successes": successes,
            "success_rate": successes / len(rows),

            "avg_latency": sum(
                r["metrics"]["latency_seconds"]
                for r in rows
            ) / len(rows),

            "avg_llm_calls": sum(
                r["metrics"]["llm_calls"]
                for r in rows
            ) / len(rows),

            "avg_tokens": sum(
                r["metrics"]["total_tokens"]
                for r in rows
            ) / len(rows),
        }

    return table


def markdown(table):

    lines = [
        "# WanderPathA Benchmark",
        "",
        "| Method | Success | LLM Calls | Tokens | Latency |",
        "|---|---:|---:|---:|---:|",
    ]

    for method, row in table.items():

        lines.append(
            f"| {method} "
            f"| {row['successes']}/{row['runs']} "
            f"| {row['avg_llm_calls']:.1f} "
            f"| {row['avg_tokens']:.0f} "
            f"| {row['avg_latency']:.2f}s |"
        )

    return "\n".join(lines)


def generate_report(results, output_dir):

    table = aggregate(results)

    report = {
        "summary": table,
    }

    json_path = output_dir / "comparison_report.json"
    md_path = output_dir / "comparison_table.md"

    json_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    md_path.write_text(
        markdown(table),
        encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(markdown(table))

    print("\nSaved:")
    print(json_path)
    print(md_path)