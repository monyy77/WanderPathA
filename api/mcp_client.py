"""
WanderPath MCP Client

Responsible for communicating with
the MCP Server and discovering tools.
"""


import asyncio



class MCPClient:


    def __init__(self, server=None):

        self.server = server



    def list_tools(self):

        """
        Runtime MCP tool discovery.

        Later connected to:
        MCP protocol client session.
        """


        if self.server is None:

            return []



        tools = asyncio.run(

            self.server.list_tools()

        )


        return tools
