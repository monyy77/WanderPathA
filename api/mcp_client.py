"""
WanderPathA MCP Client

Real FastMCP Client implementation.

Architecture:

User Platform API
        |
        v
MCPClient
        |
        v
fastmcp.Client
        |
        v
Streamable HTTP Transport
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


        # Real FastMCP Client

        self.client = Client(
            server_url
        )


        self.connected = False






    # =================================================
    # Connection Management
    # =================================================


    async def connect(self):


        if not self.connected:


            await self.client.__aenter__()


            self.connected = True








    async def disconnect(self):


        if self.connected:


            await self.client.__aexit__(
                None,
                None,
                None
            )


            self.connected = False








    # =================================================
    # MCP Tool Discovery
    # =================================================


    async def list_tools(self):


        await self.connect()



        tools = await self.client.list_tools()



        return tools







    # =================================================
    # Helper:
    # Return only tool names
    # =================================================


    async def list_tool_names(self):


        tools = await self.list_tools()



        return [

            tool.name

            for tool in tools

        ]








    # =================================================
    # MCP Tool Execution
    # =================================================


    async def call_tool(
        self,
        tool_name: str,
        arguments: dict
    ):


        await self.connect()



        result = await self.client.call_tool(

            tool_name,

            arguments

        )



        return result








    # =================================================
    # Debug
    # =================================================


    async def test_connection(self):


        tools = await self.list_tools()



        print(
            "\nAvailable MCP Tools:"
        )


        for tool in tools:


            print(
                f"- {tool.name}"
            )



        return tools
