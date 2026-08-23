"""
MCP Runtime Registry

Discovers tools dynamically
from WanderPath MCP Server.
"""


from api.mcp_client import MCPClient



class MCPRegistry:



    def __init__(self, mcp_client=None):


        self.mcp_client = (

            mcp_client

            or MCPClient()

        )





    def list_capabilities(self):


        tools = self.mcp_client.list_tools()



        capabilities = []



        for tool in tools:


            capabilities.append(

                {

                    "name":
                        tool.name,


                    "description":
                        tool.description,

                }

            )



        return capabilities





    def get_capabilities_prompt(self):


        capabilities = (

            self.list_capabilities()

        )



        return "\n".join(

            [

                f"{item['name']}: {item['description']}"

                for item in capabilities

            ]

        )
