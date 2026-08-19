from __future__ import annotations

import time
from typing import Any

from planning.self_refine import self_refine
from planning.reflexion import reflexion, ReflectionMemory
from planning.plan_and_solve import PlanAndSolvePlanner
from planning.tree_of_thoughts import TreeOfThoughtsPlanner


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


def get_output(result: Any) -> str:
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        return str(result.get("output", result))

    return str(getattr(result, "output", result))


def get_success(result: Any) -> bool:
    if isinstance(result, dict):
        return bool(result.get("success", False))

    return bool(getattr(result, "success", False))


def get_metrics(result: Any) -> tuple[int, int]:
    if isinstance(result, dict):
        return (
            int(result.get("llm_calls", 0)),
            int(result.get("tokens", 0)),
        )

    return (
        int(getattr(result, "llm_calls", 0)),
        int(getattr(result, "tokens", 0)),
    )


async def run_one(case, method: str, context: dict) -> dict:

    start = time.perf_counter()
    error = None

    try:
        goal = case.goal
        llm = context["llm"]
        registry = context["registry"]
        environment = context["environment"]

        # -----------------------------
        # Decomposition First
        # -----------------------------
        if method == "decomposition_first":

            from planning.decomposition import (
                decompose_goal,
                execute_plan,
                final_output,
            )

            plan = decompose_goal(
                goal,
                llm,
                list(registry.tools.keys()),
            )

            # Use Plan-and-Solve for "planned" DAG nodes.
            async def planner_executor(task, outputs, plan_goal):
                planner = PlanAndSolvePlanner(llm, registry)
                return await planner.run(
                    task.id,
                    task.instruction,
                )

            outputs = await execute_plan(
                plan,
                llm,
                registry.tools,
                planner_executor=planner_executor,
            )

            result = {
                "success": bool(final_output(plan, outputs)),
                "output": final_output(plan, outputs),
            }

        # -----------------------------
        # Dynamic Decomposition
        # -----------------------------
        elif method == "dynamic":

            from planning.dynamic_decomposition import (
                dynamic_decomposition,
            )

            history = await dynamic_decomposition(
                goal,
                llm,
                registry.tools,
            )

            output = history[-1][2] if history else ""

            result = {
                "success": bool(output),
                "output": output,
                "llm_calls": len(history),
            }

        # -----------------------------
        # Plan and Solve
        # -----------------------------
        elif method == "plan_and_solve":

            planner = PlanAndSolvePlanner(
                llm,
                registry,
            )

            result = await planner.run(
                case.id,
                goal,
            )

        # -----------------------------
        # Tree of Thoughts
        # -----------------------------
        elif method == "tree_of_thoughts":

            planner = TreeOfThoughtsPlanner(
                llm,
                registry,
            )

            result = await planner.run(
                case.id,
                goal,
            )

        # -----------------------------
        # LATS
        # -----------------------------
        elif method == "lats":

            from planning.lats import lats

            result = await lats(
                goal,
                llm,
                environment,
            )

        # -----------------------------
        # Ungrounded LATS
        # -----------------------------
        elif method == "lats_ungrounded":

            from planning.lats import lats

            result = await lats(
                goal,
                llm,
                None,
            )

        # -----------------------------
        # Self Refine
        # -----------------------------
        elif method == "self_refine":

            result = await self_refine(
                goal=goal,
                draft="",
                llm=llm,
                environment=environment,
            )

        # -----------------------------
        # Reflexion
        # -----------------------------
        elif method == "reflexion":

            result = await reflexion(
                goal=goal,
                llm=llm,
                environment=environment,
                initial_draft="",
                max_trials=3,
                memory=ReflectionMemory(max_items=5),
            )

        else:
            raise ValueError(f"Unknown method: {method}")

        actual_success = get_success(result)

        # For T5 expected_success=False.
        success = actual_success == case.expected_success

        llm_calls, tokens = get_metrics(result)

        output = get_output(result)

    except Exception as e:
        success = False
        llm_calls = 0
        tokens = 0
        output = ""
        error = str(e)

    latency = time.perf_counter() - start

    return {
        "case_id": case.id,
        "category": case.category,
        "method": method,
        "success": success,
        "metrics": {
            "llm_calls": llm_calls,
            "total_tokens": tokens,
            "latency_seconds": latency,
        },
        "output": output,
        "error": error,
    }


async def run_benchmark(
    cases,
    context,
    methods=None,
):

    methods = methods or METHODS
    results = []

    total = len(cases) * len(methods)
    count = 0

    print("\n" + "=" * 60)
    print("WANDERPATHA BENCHMARK")
    print("=" * 60)

    for case in cases:

        print(f"\n{case.id}: {case.category}")

        for method in methods:

            count += 1
            print(
                f"  [{count}/{total}] {method} ...",
                end=" ",
                flush=True,
            )

            result = await run_one(
                case,
                method,
                context,
            )

            results.append(result)

            print(
                "PASS"
                if result["success"]
                else "FAIL"
            )

            if result["error"]:
                print(
                    f"      {result['error']}"
                )

    print("\n" + "=" * 60)
    print("BENCHMARK DONE")
    print("=" * 60)

    return results