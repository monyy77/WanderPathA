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
    llm_calls: int



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


    llm_calls = 0



    # -------------------------
    # 1. Evaluate draft
    # -------------------------

    try:

        first_feedback = await environment.evaluate(
            candidate=draft,
            task=task,
            tool_name=tool_name,
        )

    except Exception as e:

        first_feedback = {
            "success": False,
            "error": str(e),
        }



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


    response = await llm.ainvoke(
        prompt
    )


    llm_calls += 1



    revised = getattr(
        response,
        "content",
        str(response),
    )



    # -------------------------
    # 3. Evaluate revision
    # -------------------------

    try:

        final_feedback = await environment.evaluate(
            candidate=revised,
            task=task,
            tool_name=tool_name,
        )

    except Exception as e:

        final_feedback = {
            "success": False,
            "error": str(e),
        }



    # Handle both:
    # - EvaluationResult objects
    # - Dictionary error responses

    if isinstance(
        final_feedback,
        dict
    ):

        success = final_feedback.get(
            "success",
            False
        )

    else:

        success = getattr(
            final_feedback,
            "success",
            False
        )



    return SelfRefineResult(

        goal=goal,

        draft=draft,

        critique=(
            "Revision generated using "
            "environment feedback."
        ),

        revised=revised,

        initial_feedback=first_feedback,

        final_feedback=final_feedback,

        success=success,

        llm_calls=llm_calls,

    )
