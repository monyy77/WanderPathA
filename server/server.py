# Initialize FastMCP server for WanderPathA
mcp = FastMCP("WanderPathA Travel Agent Server")



# =========================================================
# MCP Runtime Tool Discovery Interface
# =========================================================
#
# Used by AgentRouter / MCP Client
# to discover available capabilities
# dynamically at runtime.
#
# Flow:
#
# AgentRouter
#      |
#      v
# MCP Client
#      |
#      v
# get_registered_tools()
#      |
#      v
# MCP Server tools/list
#
# =========================================================


async def get_registered_tools():

    """
    Return currently available MCP tools.

    This exposes runtime tool discovery
    for the AgentRouter.

    Includes:
    - Core tools
    - Planning tools
    - Refund tools
    - VIP tools (after unlock)
    """

    return await mcp.list_tools()
