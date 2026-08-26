from __future__ import annotations
import asyncio
import time
from typing import Any

from planning.self_refine import self_refine
from planning.reflexion import reflexion, ReflectionMemory
from planning.plan_and_solve import PlanAndSolvePlanner
from planning.tree_of_thoughts import TreeOfThoughtsPlanner
from planning.lats import LATSPlanner


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

    for attr in ("output", "revised", "final_answer"):
        value = getattr(result, attr, None)
        if value is not None:
            return str(value)

    return str(result)


def get_success(result: Any) -> bool:
    if isinstance(result, dict):
        return bool(result.get("success", False))

    # Self-Refine
    if hasattr(result, "success"):
        return bool(result.success)

    # Reflexion
    if hasattr(result, "successful"):
        return bool(result.successful)

    return False


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

        # =========================================================
        # DECOMPOSITION FIRST
        # =========================================================
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

            output = final_output(plan, outputs)

            result = {
                "success": bool(output),
                "output": output,
            }

        # =========================================================
        # DYNAMIC
        # =========================================================
        elif method == "dynamic":

            from planning.dynamic_decomposition import dynamic_decomposition

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

        # =========================================================
        # PLAN AND SOLVE
        # =========================================================
        elif method == "plan_and_solve":

            planner = PlanAndSolvePlanner(
                llm,
                registry,
            )

            result = await planner.run(
                case.id,
                goal,
            )

        # =========================================================
        # TREE OF THOUGHTS
        # =========================================================
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

            from planning.lats import LATSPlanner
            from planning.schema import LATSNode, PlannerResult, PlannerType

            planner = LATSPlanner(
                llm=llm,
                tool_registry=registry,
                environment=environment,
            )

            root = LATSNode(
                id="root",
                thought=goal,
            )

            # IMPORTANT:
            # Use only 1 iteration during benchmark.
            # The original LATS.run() uses 5 iterations.
            best_node = await planner.search(
                root,
                iterations=1,
            )
            result = PlannerResult(
                success=best_node.reward > 0,
                planner=PlannerType.LATS,
                task_id=case.id,
                output=str(best_node.execution_result),
                metadata={
                    "selected_node": best_node.id,
                    "reward": best_node.reward,
                    "feedback": best_node.feedback,
                },
            )

        # -----------------------------
        # Ungrounded LATS
        # -----------------------------
        elif method == "lats_ungrounded":

            from planning.lats import LATSPlanner

            # Ungrounded LATS:
            # use a dummy environment that does not represent
            # the real MCP environment.

            class UngroundedEnvironment:

                async def evaluate(
                    self,
                    candidate,
                    task,
                    execution_result=None,
                    tool_name=None,
                ):
                    from planning.environment import EnvironmentFeedback

                    return EnvironmentFeedback(
                        success=execution_result is not None,
                        score=1.0 if execution_result is not None else 0.0,
                        details=[
                            "Ungrounded evaluation: "
                            "no real environment validation."
                        ],
                    )

            planner = LATSPlanner(
                llm=llm,
                tool_registry=registry,
                environment=UngroundedEnvironment(),
            )

            result = await planner.run(
                case.id,
                goal,
            )
        # -----------------------------
        # Self Refine
        # -----------------------------
        elif method == "self_refine":

            result = await self_refine(
                goal=goal,
                draft=goal,
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
                initial_draft=goal,
                max_trials=1,
                memory=ReflectionMemory(),
            )

        else:
            raise ValueError(f"Unknown method: {method}")

        actual_success = get_success(result)

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

            # prevent immediate rate-limit bursts from the provider
            await asyncio.sleep(20)

    print("\n" + "=" * 60)
    print("BENCHMARK DONE")
    print("=" * 60)

    return results