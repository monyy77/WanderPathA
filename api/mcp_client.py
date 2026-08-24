"""
WanderPathA MCP Client

Responsible for communicating with
the WanderPath MCP Server.

Flow:

AgentRouter
      |
      v
MCPRegistry
      |
      v
MCPClient
      |
      v
FastMCP Client
      |
      v
server.py
"""


from fastmcp import Client



class MCPClient:



    def __init__(
        self,
        server_url="http://localhost:8080"
    ):


        self.server_url = server_url


        # FastMCP official client

        self.client = Client(

            server_url

        )





    # =================================================
    # Tool Discovery
    # =================================================


    async def list_tools(self):


        """
        Discover tools dynamically
        from MCP Server.

        Equivalent to MCP:
        
        tools/list
        """


        async with self.client as client:


            tools = await client.list_tools()



            return [

                {

                    "name":
                        tool.name,


                    "description":
                        tool.description

                }

                for tool in tools

            ]






    # =================================================
    # Tool Calling
    # =================================================


    async def call_tool(
        self,
        tool_name,
        arguments=None
    ):


        """
        Execute an MCP tool.

        Only tools returned from
        list_tools() should be called.
        """


        async with self.client as client:


            result = await client.call_tool(

                tool_name,

                arguments or {}

            )


            return result
