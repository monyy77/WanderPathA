from typing import Any


class MCPToolRegistry:

    def __init__(self, mcp_client_or_tools: Any):
        """
        Initializes the registry and prepares self.tools dictionary.
        Supports passing a dict, a list of LangChain tools, or an MCP client.
        """
        self.tools = {}

        if isinstance(mcp_client_or_tools, dict):
            self.tools = mcp_client_or_tools

        elif isinstance(mcp_client_or_tools, list):
            self.tools = {
                tool.name: tool
                for tool in mcp_client_or_tools
            }

        else:
            self.mcp_client = mcp_client_or_tools

            last_tools = getattr(
                mcp_client_or_tools,
                "last_tools",
                {}
            )

            if isinstance(last_tools, list):
                self.tools = {
                    tool.name: tool
                    for tool in last_tools
                }

            elif isinstance(last_tools, dict):
                self.tools = last_tools



    def list_tools(self):
        """Get available tools from registry"""
        return list(
            self.tools.values()
        )



    def has_tool(
        self,
        tool_name: str
    ) -> bool:
        """
        Check whether a tool exists in MCP registry.
        """

        return tool_name in self.tools



    async def execute(
        self,
        tool_name: str,
        args: dict
    ):
        """
        Execute tool call on MCP Server using LangChain interface.
        """

        tool = self.tools.get(
            tool_name
        )

        if not tool:
            raise ValueError(
                f"Tool '{tool_name}' not found in registry. "
                f"Available tools: {list(self.tools.keys())}"
            )

        return await tool.ainvoke(
            args
        )
