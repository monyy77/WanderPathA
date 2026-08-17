from typing import Any


class MCPToolRegistry:

    def __init__(self, mcp_client):
        self.mcp_client = mcp_client


    def list_tools(self):
        """
        Get available tools from MCP Server
        """
        return self.mcp_client.list_tools()



    class MCPToolRegistry:


        def __init__(
            self,
            mcp_client
        ):
            self.mcp_client = mcp_client



        async def execute(
            self,
            tool_name: str,
            args: dict
        ):

            return await self.mcp_client.call_tool(
                tool_name,
                args
            )
