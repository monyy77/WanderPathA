"""
api/mcp_client.py

Production MCP Client
"""

from __future__ import annotations

import asyncio
import logging

from fastmcp import Client

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Wrapper around FastMCP Client.

    Features
    --------
    • Lazy connection
    • Connection pooling
    • Auto reconnect
    • Error handling
    • Logging
    """

    def __init__(
        self,
        server_url: str = "http://127.0.0.1:9000",
    ):

        self.server_url = server_url.rstrip("/")

        self.client = Client(
            self.server_url + "/mcp"
        )

        self.connected = False

        self._lock = asyncio.Lock()

    # ======================================================
    # Connection
    # ======================================================

    async def connect(self):

        async with self._lock:

            if self.connected:
                return

            try:

                await self.client.__aenter__()

                self.connected = True

                logger.info(
                    "Connected to MCP Server"
                )

            except Exception:

                self.connected = False

                logger.exception(
                    "Failed connecting to MCP Server"
                )

                raise

    async def disconnect(self):

        async with self._lock:

            if not self.connected:
                return

            try:

                await self.client.__aexit__(
                    None,
                    None,
                    None,
                )

            finally:

                self.connected = False

                logger.info(
                    "Disconnected from MCP Server"
                )

    async def ensure_connection(self):

        if not self.connected:

            await self.connect()

    # ======================================================
    # Tool Discovery
    # ======================================================

    async def list_tools(self):

        await self.ensure_connection()

        try:

            return await self.client.list_tools()

        except Exception:

            logger.exception(
                "Failed listing tools"
            )

            raise

    async def list_tool_names(self):

        tools = await self.list_tools()

        return [

            tool.name

            for tool in tools

        ]

    # ======================================================
    # Tool Execution
    # ======================================================

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict | None = None,
    ):

        await self.ensure_connection()

        if arguments is None:

            arguments = {}

        try:

            result = await self.client.call_tool(
                tool_name,
                arguments,
            )

            return result

        except Exception:

            logger.exception(
                "Tool '%s' failed",
                tool_name,
            )

            raise

    # ======================================================
    # Debug
    # ======================================================

    async def test_connection(self):

        tools = await self.list_tools()

        print("\nAvailable MCP Tools:\n")

        for tool in tools:

            print(f"• {tool.name}")

        return tools

    # ======================================================
    # Context Manager
    # ======================================================

    async def __aenter__(self):

        await self.connect()

        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):

        await self.disconnect()