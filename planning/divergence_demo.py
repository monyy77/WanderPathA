"""
Divergence demo: decomposition-first vs. dynamic decomposition, run
against two real cases already present in db/data.sql, reporting real
token usage and context-size numbers -- not just the theoretical
description in planning/README.md.

Backs this exact requirement from the task description:
    "Show a real case where the two methods diverge ... but also show
    token usage and if the tests you wrote for your agent resulted in
    bigger context."

Uses ONLY existing seed data (no new rows added to db/data.sql):

Case A -- favors dynamic (Flight 3, DXB -> LHR, Cancelled due to a
technical issue; zero other flights exist on that route in db/data.sql,
so get_flight_options genuinely returns empty). Decomposition-first
commits to a rebooking-proposal node before knowing alternatives are
empty; dynamic decomposition observes the empty result live and reroutes
to alternative transport / escalation instead.

Case B -- the comparatively simpler existing case (Flight 2, CAI -> JED,
120-minute weather delay). It still has a VIP passenger and a
connection-risk flag, so the contrast with Case A is smaller than an
artificially "clean" case would show -- but every number here comes from
data the team already had, with nothing added for this demo.

Usage (from the repo root, MCP server running, .env configured):
    python planning/divergence_demo.py

Writes planning/divergence_demo_report.json with the full numbers behind
the summary this script prints.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from client.client import create_client
from planning.planning_agent import run_planning_agent

CASES = {
    "case_a_favors_dynamic": (
        "Flight 3 (DXB to LHR) has been cancelled due to a technical issue. "
        "Reshuffle every booking affected by this disruption: assess "
        "priority, find rebooking or transport alternatives, and propose a "
        "plan per customer including any compensation owed."
    ),
    "case_b_existing_moderate_delay": (
        "Flight 2 (CAI to JED) has been delayed 120 minutes due to bad "
        "weather, with a high connection-risk flag. Reshuffle every "
        "booking affected by this disruption: assess priority, find "
        "rebooking or transport alternatives, and propose a plan per "
        "customer including any compensation owed."
    ),
}


async def run_case(client, label: str, goal: str) -> dict:
    modes_report = {}
    for mode in ("decomposition_first", "dynamic"):
        result = await run_planning_agent(client, goal, mode=mode)
        usage = result["token_usage"]
        modes_report[mode] = {
            "llm_calls": usage["llm_calls"],
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "total_tokens": usage["total_tokens"],
            "peak_single_call_input_tokens": usage["peak_input_tokens"],
            "latency_seconds": result["latency_seconds"],
            "result_preview": result["result"][:300],
            "artifact_path": result["artifact_path"],
        }
    return {"case": label, "goal": goal, "modes": modes_report}


def print_case_summary(case_report: dict) -> None:
    print(f"\n=== {case_report['case']} ===")
    print(f"Goal: {case_report['goal']}\n")
    df, dy = case_report["modes"]["decomposition_first"], case_report["modes"]["dynamic"]
    print(f"{'metric':<28}{'decomposition_first':<22}{'dynamic'}")
    print(f"{'llm_calls':<28}{df['llm_calls']:<22}{dy['llm_calls']}")
    print(f"{'total_tokens':<28}{df['total_tokens']:<22}{dy['total_tokens']}")
    print(f"{'peak_input_tokens':<28}{df['peak_single_call_input_tokens']:<22}{dy['peak_single_call_input_tokens']}")
    print(f"{'latency_seconds':<28}{df['latency_seconds']:<22}{dy['latency_seconds']}")

    bigger_context = "dynamic" if dy["peak_single_call_input_tokens"] > df["peak_single_call_input_tokens"] else "decomposition_first"
    print(f"\n-> Bigger single-call context in this case: {bigger_context}")


async def main() -> None:
    client = await create_client()
    try:
        report = []
        for label, goal in CASES.items():
            case_report = await run_case(client, label, goal)
            report.append(case_report)
            print_case_summary(case_report)

        out_path = Path(__file__).resolve().parent / "divergence_demo_report.json"
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nFull report saved: {out_path}")
    finally:
        if hasattr(client, "close"):
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
