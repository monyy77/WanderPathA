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
        #
        # If an external registry is passed
        # use it.
        #
        # Otherwise create one that uses
        # MCP Client internally.

        self.mcp_registry = (

            mcp_registry

            or MCPRegistry()

        )





    # =================================================
    # Capability Classification
    # =================================================


    def classify(self, message: str):


        # Discover MCP tools dynamically

        capabilities = (

            self.mcp_registry
            .get_capabilities_prompt()

        )



        # If LLM is not configured,
        # fallback will handle routing

        if self.llm is None:

            return None





        prompt = f"""

You are a routing agent.

Your task is to select exactly ONE
capability from the available MCP tools.

Available MCP capabilities:

{capabilities}


User request:

{message}


Rules:

- Select only from the provided capabilities.
- Never invent a capability.
- Return only valid JSON.


Required format:

{{
    "capability":
    "exact_capability_name"
}}

"""



        response = self.llm.invoke(

            prompt

        )





        try:


            # Parse LLM JSON response

            data = json.loads(

                response.content

            )



            capability = data.get(

                "capability"

            )





            # Validate against
            # runtime MCP capabilities

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





        # Invalid response
        # AgentRouter will use fallback

        return None
