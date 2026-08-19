from __future__ import annotations

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from planning_eval.test_cases import TEST_CASES
from planning_eval.evaluator import run_benchmark

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "evaluation_results.json"


async def main():

    print("\nStarting WanderPathA evaluation...")

    # =====================================================
    # CREATE MCP CLIENT + KEEP SESSION ALIVE
    # =====================================================

    from client.client import create_client
    from agent.agent import build_structured_model, discover_tools

    from planning.environment import TravelEnvironment
    from planning.tool_registry import MCPToolRegistry

    # create_client() currently manages the MCP session internally,
    # so we need to modify client.py slightly (see below).

    client = await create_client()

    # Get tools from the active MCP client/session
    mcp_tools = await discover_tools(client)

    print(f"\nLoaded {len(mcp_tools)} MCP tools:")
    for name in mcp_tools:
        print(f"  - {name}")

    # =====================================================
    # PLANNING COMPONENTS
    # =====================================================

    registry = MCPToolRegistry(mcp_tools)

    environment = TravelEnvironment(
        mcp_tools=mcp_tools,
    )

    llm = build_structured_model(
        list(mcp_tools.keys())
    )

    context = {
        "llm": llm,
        "registry": registry,
        "environment": environment,
        "mcp_tools": mcp_tools,
    }

    # =====================================================
    # RUN BENCHMARK
    # =====================================================

    results = await run_benchmark(
        cases=TEST_CASES,
        context=context,
    )

    # =====================================================
    # SAVE RESULTS
    # =====================================================

    RESULTS.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    print("\nResults saved to:")
    print(RESULTS)

    # =====================================================
    # COMPARISON
    # =====================================================

    from planning_eval.comparison import generate_report

    generate_report(
        results,
        ROOT,
    )


if __name__ == "__main__":
    asyncio.run(main())