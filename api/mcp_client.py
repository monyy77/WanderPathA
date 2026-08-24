"""
WanderPathA MCP Client

Real MCP client implementation.

Connects to:

User Platform
        |
        v
FastMCP Client
        |
        v
WanderPath MCP Server
"""


from fastmcp import Client



class MCPClient:



    def __init__(
        self,
        server_url="http://localhost:8080"
    ):


        self.server_url = server_url



        self.client = Client(
            server_url
        )






    # =================================================
    # Discover MCP Tools
    # =================================================


    async def list_tools(self):


        async with self.client as client:


            tools = await client.list_tools()



            return tools







    # =================================================
    # Execute MCP Tool
    # =================================================


    async def call_tool(
        self,
        tool_name: str,
        arguments: dict
    ):



        async with self.client as client:


            result = await client.call_tool(

                tool_name,

                arguments

            )



            return result
