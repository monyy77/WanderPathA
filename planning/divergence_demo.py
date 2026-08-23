"""
Divergence demo: decomposition-first vs. dynamic decomposition.

Runs two real IROPS disruption cases using the existing WanderPathA
database/MCP server and compares:

- LLM calls
- Token usage
- Context size
- Latency
- Final outputs

Requirement demonstrated:
    "Show a real case where the two methods diverge and report
    token usage/context differences."

Uses ONLY existing seed data.

Case A -- favors dynamic decomposition:
    Flight 3 (DXB -> LHR) is cancelled due to a technical issue.
    No alternative flights exist on this route in the database.

    Decomposition-first:
        Commits early to a generated plan.

    Dynamic decomposition:
        Observes empty alternatives and can adapt/re-route.

Case B -- moderate delay:
    Flight 2 (CAI -> JED) has a 120-minute weather delay.
    Used as a comparison case.

Usage:
    python planning/divergence_demo.py

Output:
    planning/divergence_demo_report.json
"""


from __future__ import annotations


import asyncio
import json

from pathlib import Path


from client.client import create_client

from planning.planning_agent import (
    run_planning_agent
)



CASES = {

    "case_a_favors_dynamic": (

        "Flight 3 (DXB to LHR) has been cancelled due to a "
        "technical issue. Reshuffle every booking affected "
        "by this disruption: assess priority, find "
        "rebooking or transport alternatives, and propose "
        "a plan per customer including any compensation owed."

    ),


    "case_b_existing_moderate_delay": (

        "Flight 2 (CAI to JED) has been delayed 120 minutes "
        "due to bad weather, with a high connection-risk "
        "flag. Reshuffle every booking affected by this "
        "disruption: assess priority, find rebooking or "
        "transport alternatives, and propose a plan per "
        "customer including any compensation owed."

    ),

}



async def run_mode(
    goal: str,
    mode: str,
) -> dict:

    """
    Run one planning mode with an isolated MCP client.

    Isolation is important because:
        - memory/state should not leak
        - token measurements remain comparable
        - MCP sessions remain independent
    """


    client = await create_client()


    try:

        result = await run_planning_agent(

            client,

            goal,

            mode=mode

        )


        usage = result["token_usage"]


        return {

            "llm_calls":
                usage["llm_calls"],


            "input_tokens":
                usage["input_tokens"],


            "output_tokens":
                usage["output_tokens"],


            "total_tokens":
                usage["total_tokens"],


            "peak_single_call_input_tokens":
                usage["peak_input_tokens"],


            "latency_seconds":
                result["latency_seconds"],


            "result_preview":
                result["result"][:300],


            "artifact_path":
                result["artifact_path"],

        }


    finally:

        if hasattr(
            client,
            "close"
        ):

            await client.close()





async def run_case(
    label: str,
    goal: str,
) -> dict:


    modes_report = {}


    for mode in (

        "decomposition_first",

        "dynamic",

    ):


        modes_report[mode] = await run_mode(

            goal,

            mode

        )


    return {

        "case":
            label,


        "goal":
            goal,


        "modes":
            modes_report,

    }





def print_case_summary(
    case_report: dict
):


    print(
        f"\n=== {case_report['case']} ==="
    )


    print(
        f"Goal:\n{case_report['goal']}\n"
    )


    decomposition = case_report["modes"][
        "decomposition_first"
    ]


    dynamic = case_report["modes"][
        "dynamic"
    ]



    print(
        f"{'metric':<35}"
        f"{'decomposition_first':<25}"
        f"{'dynamic'}"
    )


    print(
        f"{'llm_calls':<35}"
        f"{decomposition['llm_calls']:<25}"
        f"{dynamic['llm_calls']}"
    )


    print(
        f"{'total_tokens':<35}"
        f"{decomposition['total_tokens']:<25}"
        f"{dynamic['total_tokens']}"
    )


    print(
        f"{'peak_input_tokens':<35}"
        f"{decomposition['peak_single_call_input_tokens']:<25}"
        f"{dynamic['peak_single_call_input_tokens']}"
    )


    print(
        f"{'latency_seconds':<35}"
        f"{decomposition['latency_seconds']:<25}"
        f"{dynamic['latency_seconds']}"
    )



    if (

        dynamic["peak_single_call_input_tokens"]

        >

        decomposition["peak_single_call_input_tokens"]

    ):

        bigger_context = "dynamic"


    else:

        bigger_context = "decomposition_first"



    print(
        "\n-> Bigger single-call context: "
        f"{bigger_context}"
    )





async def main():


    report = []


    for label, goal in CASES.items():


        case_report = await run_case(

            label,

            goal

        )


        report.append(
            case_report
        )


        print_case_summary(
            case_report
        )



    out_path = (

        Path(__file__)
        .resolve()
        .parent
        /
        "divergence_demo_report.json"

    )


    out_path.write_text(

        json.dumps(

            report,

            indent=2,

            ensure_ascii=False,

        ),

        encoding="utf-8"

    )


    print(
        "\nFull report saved:"
        f" {out_path}"
    )





if __name__ == "__main__":

    asyncio.run(
        main()
    )
