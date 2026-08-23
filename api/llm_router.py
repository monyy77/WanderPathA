"""
MCP Aware LLM Router

LLM chooses only from
runtime discovered MCP capabilities.
"""


import json


from api.mcp_registry import MCPRegistry



class LLMRouter:


    def __init__(
        self,
        llm=None,
        mcp_registry=None
    ):

        self.llm = llm

        self.mcp_registry = (
            mcp_registry
            or MCPRegistry()
        )



    def classify(self, message):


        capabilities = (

            self.mcp_registry
            .get_capabilities_prompt()

        )



        if self.llm is None:

            return None



        prompt = f"""

You are a routing agent.

Select ONE capability.

Available MCP capabilities:

{capabilities}


User request:

{message}


Return ONLY JSON:

{{
"capability":
"exact_name_from_list"
}}

"""



        response = self.llm.invoke(
            prompt
        )



        try:

            data = json.loads(
                response.content
            )


            capability = data.get(
                "capability"
            )


            available = [

                item["name"]

                for item

                in self.mcp_registry
                .list_capabilities()

            ]


            if capability in available:

                return capability



        except Exception:

            pass



        return None
