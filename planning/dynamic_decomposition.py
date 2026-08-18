"""
Dynamic / interleaved decomposition: generate the next sub-task only after
observing the result of the last one, so an early surprise (e.g. "no
alternative flights available") can change what comes next, instead of
blindly executing a plan made before that surprise was known.

FORKED FROM: AmrSheta22/task_decomposition_and_planning
             planning_lab/algorithms/dynamic_decomposition.py
Credit: the decide -> execute -> observe loop and the `DynamicDecision`
schema are the toolkit's. Two changes were needed for a real IROPS agent
rather than the toolkit's generic text-only demo:

  1. The "execute" step is no longer always an LLM call. The planner can
     pick a real MCP tool by name (`next_tool`), and `dynamic_decomposition`
     invokes it directly against the live DB, exactly like a TOOL_CALL node
     in decomposition.py. This is what lets the loop actually *observe* a
     grounded fact (e.g. an empty alternative-flights list) instead of an
     LLM's guess about one.
  2. The planner is told which tools exist so `next_tool` is always a real,
     callable name, never a hallucinated one.

See planning_agent.py for the concrete divergence case this is built to
show against decomposition.py: a disrupted flight with zero available
alternative flights, where decomposition-first commits to a rebooking node
before knowing that, and this loop reacts to it live.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, ConfigDict

DYNAMIC_SYSTEM = """You are an adaptive IROPS planner. Use prior observations
before deciding what comes next -- do not repeat a lookup you already have the
answer to. Prefer a tool_call whenever the next step is a real lookup; use
reasoning only for judgment calls over information you already have.
Set done to true only when you have enough to propose a final rebooking plan
for every affected booking."""


class DynamicDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    done: bool
    next_kind: str = "reasoning"  # "tool_call" | "reasoning"
    next_tool: str | None = None  # required when next_kind == "tool_call"
    next_task: str  # instruction text, or JSON args when next_kind == tool_call


async def dynamic_decomposition(
    goal: str,
    llm: BaseChatModel,
    mcp_tools: dict[str, Any],
    max_steps: int = 6,
) -> list[tuple[str, str, str]]:
    """Returns a history of (kind, task_description, observed_result)."""
    history: list[tuple[str, str, str]] = []
    tool_names = "\n".join(f"- {n}" for n in mcp_tools)

    for step in range(max_steps):
        observation = (
            "\n".join(f"[{kind}] {task}: {result}" for kind, task, result in history)
            or "None"
        )
        decision = llm.with_structured_output(
            DynamicDecision,
            method="json_schema",
        ).invoke(
            [
                ("system", DYNAMIC_SYSTEM + f"\n\nAvailable tools:\n{tool_names}"),
                (
                    "human",
                    f"""Goal: {goal}
Completed work and observations so far:
{observation}

Decide the single best next step.""",
                ),
            ],
            temperature=0.1,
        )

        if decision.done:
            break

        task = decision.next_task.strip()
        if not task:
            raise ValueError(f"Dynamic planner omitted next_task at step {step + 1}")

        if decision.next_kind == "tool_call":
            tool = mcp_tools.get(decision.next_tool)
            if tool is None:
                raise RuntimeError(
                    f"Dynamic planner picked unknown tool '{decision.next_tool}' at step {step + 1}"
                )
            try:
                args = json.loads(task)
            except json.JSONDecodeError:
                args = {}
            result = str(await tool.ainvoke(args))
        else:
            response = await llm.ainvoke(
                [
                    ("system", "Execute the next adaptive sub-task using the observations provided."),
                    ("human", f"Goal: {goal}\nNext task: {task}\nPrior observations:\n{observation}"),
                ],
                temperature=0.2,
            )
            result = response.content
            if not isinstance(result, str) or not result.strip():
                raise RuntimeError("The chat model returned an empty or unsupported response")
            result = result.strip()

        history.append((decision.next_kind, task, result))

    return history
