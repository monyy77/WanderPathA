"""
MCP Aware LLM Router

LLM chooses only from
runtime discovered MCP capabilities.

Flow:

User Message
      |
      v
LLM Router
      |
      v
MCP Registry
      |
      v
Runtime MCP Tools
      |
      v
Validated Capability
"""


import json


from api.mcp_registry import MCPRegistry





class LLMRouter:



    def __init__(
        self,
        llm=None,
        mcp_registry=None
    ):


        # LLM instance

        self.llm = llm



        # Runtime MCP Registry

        self.mcp_registry = (

            mcp_registry

            or MCPRegistry()

        )







    # =================================================
    # Capability Classification
    # =================================================


    async def classify(
        self,
        message: str
    ):


        # -----------------------------------------
        # Discover runtime MCP tools
        # -----------------------------------------

        capabilities = (

            await self.mcp_registry
            .get_capabilities_prompt()

        )



        # If LLM unavailable
        # AgentRouter fallback handles routing

        if self.llm is None:

            return None





        prompt = f"""

You are a routing agent.

Select exactly ONE capability
from the available MCP tools.

Available MCP capabilities:

{capabilities}


User request:

{message}


Rules:

- Choose only existing MCP capabilities.
- Never invent tools.
- Return only JSON.


Format:

{{
    "capability":
    "exact_tool_name"
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




            # -----------------------------------------
            # Runtime validation
            # -----------------------------------------

            available = [

                item["name"]

                for item

                in await self.mcp_registry
                .list_capabilities()

            ]



            if capability in available:


                return capability





        except Exception:


            pass





        return None
