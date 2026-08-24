"""
mcp_server/server.py

Main FastMCP server.

Responsible for:

- Creating MCP server
- Registering tools
- Running transport
"""


import sys
import os


sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)



from mcp.server.fastmcp import FastMCP



# ==========================================================
# Create MCP Server
# ==========================================================


mcp = FastMCP(

    name="WanderPathA Travel Agent Server",

    host="127.0.0.1",

    port=9000,
)



# ==========================================================
# Health Check Tool
# ==========================================================


@mcp.tool()
def ping():

    """
    Test MCP connection.
    """

    return "pong"




# ==========================================================
# Register Runtime Tools
# ==========================================================


def register_all_tools():

    """
    Register LangChain tools inside MCP.
    """

    from mcp_server.register_tools import (
        register_runtime_tools
    )


    register_runtime_tools(
        mcp
    )




# ==========================================================
# Tool Discovery
# ==========================================================


async def get_registered_tools():

    """
    Return MCP registered tools.
    """

    return await mcp.list_tools()




# ==========================================================
# Main Entry
# ==========================================================


if __name__ == "__main__":


    print(
        "Starting WanderPathA MCP Server..."
    )


    register_all_tools()


    print(
        "MCP Server Ready"
    )


    mcp.run(
        transport="streamable-http"
    )