import os
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

SERVER_PATH = os.path.join(PROJECT_ROOT, "server", "server.py")


async def call_mcp_tool(tool_name: str, **kwargs):
    client = MultiServerMCPClient({
        "wanderpath_server": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["-m", "server.server", "stdio"],
            "cwd": PROJECT_ROOT,
        }
    })

    async with client.session("wanderpath_server") as session:
        tools = await load_mcp_tools(session)

        tool = next(
            (t for t in tools if t.name == tool_name),
            None
        )

        if tool is None:
            raise ValueError(f"MCP tool not found: {tool_name}")

        return await tool.ainvoke(kwargs)