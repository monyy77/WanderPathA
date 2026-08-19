from dataclasses import dataclass
from typing import Any


@dataclass
class SelfRefineResult:

    goal: str
    draft: str
    critique: str
    revised: str

    initial_feedback: Any
    final_feedback: Any

    success: bool
    llm_calls: int = 2


async def self_refine(
    goal: str,
    draft: str,
    llm: Any,
    environment: Any,
    *,
    task: str | None = None,
    tool_name: str | None = None,
):

    task = task or goal

    # -------------------------
    # 1. Evaluate draft
    # -------------------------

    first_feedback = await environment.evaluate(
        candidate=draft,
        task=task,
        tool_name=tool_name,
    )

    # -------------------------
    # 2. Critique + revision
    # -------------------------

    prompt = f"""
Goal:
{goal}

Draft:
{draft}

Environment feedback:
{first_feedback}

Improve the draft.

Do not invent facts.
Use only available evidence.
Return only the improved answer.
"""

    response = llm.ainvoke(prompt)

    if hasattr(response, "__await__"):
        response = await response

    revised = getattr(
        response,
        "content",
        str(response),
    )

    # -------------------------
    # 3. Evaluate revision
    # -------------------------

    final_feedback = await environment.evaluate(
        candidate=revised,
        task=task,
        tool_name=tool_name,
    )

    return SelfRefineResult(
        goal=goal,
        draft=draft,
        critique="Improved using environment feedback.",
        revised=revised,
        initial_feedback=first_feedback,
        final_feedback=final_feedback,
        success=final_feedback.success,
    )