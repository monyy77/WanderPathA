"""
Runtime MCP Capability Validator

Validates capabilities only from
MCP Server discovered tools.
"""


class MCPCapabilityValidator:


    def __init__(
        self,
        mcp_registry
    ):

        self.mcp_registry = mcp_registry



    async def is_valid_capability(
        self,
        capability: str
    ):


        tools = (
            self.mcp_registry
            .list_capabilities()
        )


        available = [

            tool["name"]

            for tool in tools

        ]


        return capability in available
