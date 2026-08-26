from __future__ import annotations

import json


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
            bool(r["success"])
            for r in rows
        )

        total_runs = len(rows)

        total_latency = sum(
            r["metrics"].get("latency_seconds", 0)
            for r in rows
        )

        total_calls = sum(
            r["metrics"].get("llm_calls", 0)
            for r in rows
        )

        total_tokens = sum(
            r["metrics"].get("total_tokens", 0)
            for r in rows
        )

        table[method] = {
            "runs": total_runs,
            "successes": successes,
            "success_rate": successes / total_runs,

            "avg_latency": (
                total_latency / total_runs
            ),

            "avg_llm_calls": (
                total_calls / total_runs
            ),

            "avg_tokens": (
                total_tokens / total_runs
            ),

            "total_tokens": total_tokens,
            "total_llm_calls": total_calls,
        }

    return table


def markdown(table):

    lines = [
        "# WanderPathA Benchmark Comparison",
        "",
        "| Method | Success | Success Rate | Avg. LLM Calls | Avg. Tokens | Avg. Latency |",
        "|:--|--:|--:|--:|--:|--:|",
    ]

    for method, row in table.items():

        success = (
            f"{row['successes']}/{row['runs']}"
        )

        success_rate = (
            f"{row['success_rate'] * 100:.1f}%"
        )

        llm_calls = (
            f"{row['avg_llm_calls']:.1f}"
        )

        tokens = (
            f"{row['avg_tokens']:,.0f}"
        )

        latency = (
            f"{row['avg_latency']:.2f}s"
        )

        lines.append(
            f"| **{method}** "
            f"| {success} "
            f"| {success_rate} "
            f"| {llm_calls} "
            f"| {tokens} "
            f"| {latency} |"
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

    print("\n" + "=" * 80)
    print("WANDERPATHA BENCHMARK COMPARISON")
    print("=" * 80)

    print(markdown(table))

    print("\n" + "=" * 80)
    print("FILES")
    print("=" * 80)

    print(f"JSON report : {json_path}")
    print(f"Markdown    : {md_path}")