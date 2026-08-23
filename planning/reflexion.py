from dataclasses import dataclass, field
from typing import Any


MAX_REFLECTIONS = 10



@dataclass
class ReflectionMemory:

    reflections: list[str] = field(
        default_factory=list
    )


    def add(
        self,
        text: str
    ):

        if text.strip():

            self.reflections.append(
                text.strip()
            )

            self.reflections = (
                self.reflections[-MAX_REFLECTIONS:]
            )



@dataclass
class ReflexionResult:

    goal: str
    final_answer: str
    successful: bool
    trials: int
    reflections: list[str]
    llm_calls: int
    last_feedback: Any



async def reflexion(
    goal: str,
    llm: Any,
    environment: Any,
    *,
    max_trials: int = 3,
    memory: ReflectionMemory | None = None,
    task: str | None = None,
    tool_name: str | None = None,
    initial_draft: str | None = None,
):

    if memory is None:

        memory = ReflectionMemory()


    answer = initial_draft or ""

    last_feedback = None

    calls = 0



    for trial in range(
        1,
        max_trials + 1
    ):


        prompt = f"""
Goal:
{goal}

Previous answer:
{answer}

Previous reflections:
{memory.reflections}

Create the best answer.

Do not invent facts.
Use grounded evidence.
"""


        response = await llm.ainvoke(
            prompt
        )


        answer = getattr(
            response,
            "content",
            str(response),
        )


        calls += 1



        try:

            last_feedback = await environment.evaluate(
                candidate=answer,
                task=task or goal,
                tool_name=tool_name,
            )


        except Exception as e:

            memory.add(
                f"Evaluation failed: {str(e)}"
            )

            continue



        if last_feedback.success:

            return ReflexionResult(

                goal=goal,

                final_answer=answer,

                successful=True,

                trials=trial,

                reflections=memory.reflections,

                llm_calls=calls,

                last_feedback=last_feedback,

            )



        memory.add(

            f"Trial {trial} failed: "
            f"{last_feedback.details}"

        )



    return ReflexionResult(

        goal=goal,

        final_answer=answer,

        successful=False,

        trials=max_trials,

        reflections=memory.reflections,

        llm_calls=calls,

        last_feedback=last_feedback,

    )
