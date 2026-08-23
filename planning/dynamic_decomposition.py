from __future__ import annotations


from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)



DYNAMIC_SYSTEM = """
You are an adaptive IROPS planner.

Use prior observations before deciding what comes next.

Do not repeat completed lookups.

Prefer tool_call whenever the next step requires real information.

Use reasoning only for judgment over existing observations.

Set done=true only when enough information exists
to propose a final rebooking plan.

Available tools must always be selected from the provided MCP tools.
"""



class DynamicDecision(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )


    done: bool


    next_kind: Literal[
        "tool_call",
        "reasoning"
    ] = "reasoning"


    next_tool: str | None = None


    next_task: str


    arguments: dict[str,Any] = Field(
        default_factory=dict
    )




async def dynamic_decomposition(
    goal: str,
    llm: BaseChatModel,
    mcp_tools: dict[str,Any],
    max_steps: int = 6,
) -> list[tuple[str,str,str]]:

    history: list[
        tuple[str,str,str]
    ] = []



    for step in range(max_steps):


        tool_names = "\n".join(
            f"- {name}"
            for name in mcp_tools.keys()
        )


        observation = (

            "\n".join(

                f"[{kind}] {task}: {result}"

                for kind,task,result in history

            )

            or "None"

        )



        decision = await llm.with_structured_output(
            DynamicDecision,
            method="json_schema",
        ).ainvoke(

            [

                (
                    "system",
                    DYNAMIC_SYSTEM
                    +
                    f"\n\nAvailable MCP tools:\n{tool_names}"
                ),


                (

                    "human",

                    f"""
Goal:

{goal}


Completed work and observations:

{observation}


Decide the single best next step.
"""

                )

            ],

            temperature=0.1

        )



        if decision.done:

            break



        task = decision.next_task.strip()



        if not task:

            raise ValueError(
                f"Dynamic planner omitted next_task at step {step+1}"
            )



        if decision.next_kind == "tool_call":



            if not decision.next_tool:

                raise ValueError(
                    "tool_call requires next_tool"
                )



            if decision.next_tool not in mcp_tools:

                raise RuntimeError(
                    f"Unknown MCP tool: {decision.next_tool}"
                )



            tool = mcp_tools[
                decision.next_tool
            ]



            result = await tool.ainvoke(
                decision.arguments
            )


            result = str(result)



        else:



            response = await llm.ainvoke(

                [

                    (
                        "system",
                        """
Execute one reasoning step
using only provided observations.
Do not invent information.
"""
                    ),


                    (

                        "human",

                        f"""
Goal:

{goal}


Task:

{task}


Observations:

{observation}
"""

                    )

                ],

                temperature=0.2

            )



            result = response.content



            if not isinstance(
                result,
                str
            ) or not result.strip():

                raise RuntimeError(
                    "Empty LLM response"
                )


            result = result.strip()



        history.append(

            (
                decision.next_kind,
                task,
                result
            )

        )



    return history


'''
                 Planning Agent
                      |
        --------------------------------
        |                              |
Decomposition-first          Dynamic decomposition
        |                              |
Generate full DAG             Decide next step
        |                              |
Validate DAG                  Execute
        |                              |
Execute batches               Observe result
        |                              |
TOOL/PLANNED/REASONING        Re-plan
'''
