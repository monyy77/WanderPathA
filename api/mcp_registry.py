"""
MCP Runtime Registry

Discovers capabilities
from MCP Server dynamically.
"""


class MCPRegistry:



    def __init__(
        self,
        mcp_client
    ):

        self.mcp_client = mcp_client






    async def list_capabilities(
        self
    ):



        tools = await (

            self.mcp_client

            .list_tools()

        )



        capabilities = []



        for tool in tools:


            capabilities.append(

                {

                    "name":

                        tool.name,


                    "description":

                        tool.description,



                    "input_schema":

                        tool.inputSchema,

                }

            )



        return capabilities







    async def get_capabilities_prompt(
        self
    ):



        capabilities = await (

            self.list_capabilities()

        )



        return "\n".join(

            [

                f"{item['name']}: {item['description']}"

                for item in capabilities

            ]

        )
