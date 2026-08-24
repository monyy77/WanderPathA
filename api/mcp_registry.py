"""
MCP Runtime Registry

Discovers tools dynamically
from WanderPath MCP Server.

Flow:

AgentRouter
      |
      v
MCPRegistry
      |
      v
MCPClient.list_tools()
      |
      v
FastMCP Client
      |
      v
WanderPath MCP Server tools/list
"""


from api.mcp_client import MCPClient





class MCPRegistry:



    def __init__(
        self,
        mcp_client=None
    ):


        self.mcp_client = (

            mcp_client

            or MCPClient()

        )



        # Cache discovered tools

        self._capabilities = None






    # =================================================
    # Runtime Tool Discovery
    # =================================================


    async def list_capabilities(self):


        """
        Discover MCP tools dynamically.

        Calls:

        MCP Client
             |
             v
        tools/list

        """


        tools = await self.mcp_client.list_tools()



        capabilities = []



        for tool in tools:


            capabilities.append(

                {


                    "name":

                        tool.get(

                            "name",

                            ""

                        ),



                    "description":

                        tool.get(

                            "description",

                            ""

                        ),

                }

            )



        self._capabilities = capabilities



        return capabilities







    # =================================================
    # LLM Prompt Builder
    # =================================================


    async def get_capabilities_prompt(self):


        capabilities = await self.list_capabilities()



        return "\n".join(

            [

                (
                    f"{item['name']}: "
                    f"{item['description']}"
                )

                for item in capabilities

            ]

        )
