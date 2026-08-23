"""
LLM Router

Uses LLM for intelligent agent selection.

The output is always validated
against MCP allowed agents.
"""


import json


from api.agent_registry import (
    AVAILABLE_AGENTS,
    get_agents_description,
)



class LLMRouter:


    def __init__(self, llm=None):

        self.llm = llm



    def classify(self, message: str):


        if self.llm is None:

            return None



        prompt = f"""

You are an agent router.

Choose exactly one agent.

Available agents:

{get_agents_description()}


User message:

{message}


Return ONLY JSON:

{{
"agent":"agent_name"
}}

"""


        response = self.llm.invoke(
            prompt
        )


        try:

            data = json.loads(
                response.content
            )


            agent = data.get(
                "agent"
            )


            if agent in AVAILABLE_AGENTS:

                return agent



        except Exception:

            pass



        return None
