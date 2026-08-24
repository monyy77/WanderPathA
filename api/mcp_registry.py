"""
api/mcp_registry.py

Runtime capability discovery for WanderPathA.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MCPRegistry:
    """
    Discovers capabilities dynamically from the MCP Server.

    Responsibilities
    ----------------
    • Runtime tool discovery
    • Capability caching
    • Prompt generation
    • Tool lookup
    """

    def __init__(self, mcp_client):

        self.mcp_client = mcp_client

        self._capabilities: list[dict[str, Any]] = []

    # ==========================================================
    # Discovery
    # ==========================================================

    async def refresh(self):

        """
        Refresh runtime capabilities from MCP.
        """

        tools = await self.mcp_client.list_tools()

        self._capabilities = []

        for tool in tools:

            self._capabilities.append({

                "name": tool.name,

                "description": tool.description or "",

                "input_schema": getattr(
                    tool,
                    "inputSchema",
                    {}
                ),

            })

        logger.info(
            "Discovered %d MCP tools",
            len(self._capabilities),
        )

        return self._capabilities

    async def list_capabilities(self):

        """
        Return cached capabilities.
        """

        if not self._capabilities:

            await self.refresh()

        return self._capabilities

    # ==========================================================
    # Lookup
    # ==========================================================

    async def get_capability(
        self,
        tool_name: str,
    ):

        capabilities = await self.list_capabilities()

        for capability in capabilities:

            if capability["name"] == tool_name:

                return capability

        return None

    async def has_capability(
        self,
        tool_name: str,
    ):

        capability = await self.get_capability(
            tool_name
        )

        return capability is not None

    async def list_tool_names(self):

        capabilities = await self.list_capabilities()

        return [

            item["name"]

            for item in capabilities

        ]

    # ==========================================================
    # Prompt Builder
    # ==========================================================

    async def get_capabilities_prompt(self):

        """
        Build an LLM prompt describing every available tool.
        """

        capabilities = await self.list_capabilities()

        if not capabilities:

            return "No MCP tools are currently available."

        lines = [

            "Available MCP Tools:",

            ""

        ]

        for capability in capabilities:

            lines.append(

                f"- {capability['name']}"

            )

            if capability["description"]:

                lines.append(

                    f"  Description: {capability['description']}"

                )

            if capability["input_schema"]:

                lines.append(

                    f"  Input Schema: {capability['input_schema']}"

                )

            lines.append("")

        return "\n".join(lines)

    # ==========================================================
    # Cache Management
    # ==========================================================

    def clear_cache(self):

        """
        Force capability rediscovery.
        """

        self._capabilities.clear()