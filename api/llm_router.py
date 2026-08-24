"""
api/agent_router.py

Dynamic MCP Router

Discovers tools from the MCP Server at runtime
and constrains the LLM to only those tools.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

from api.mcp_registry import MCPRegistry

logger = logging.getLogger(__name__)


# ==========================================================
# Routing Decision
# ==========================================================

@dataclass
class RoutingDecision:

    capability: Optional[str]

    confidence: float = 1.0

    reason: str = ""


# ==========================================================
# Router
# ==========================================================

class LLMRouter:

    def __init__(
        self,
        llm,
        mcp_registry: MCPRegistry,
    ):

        self.llm = llm

        self.registry = mcp_registry

    # ======================================================
    # Main Routing
    # ======================================================

    async def classify(
        self,
        message: str,
    ) -> RoutingDecision:

        capabilities = await self.registry.list_capabilities()

        if not capabilities:

            return RoutingDecision(
                capability=None,
                confidence=0,
                reason="No MCP capabilities discovered."
            )

        available_tools = [

            tool["name"]

            for tool in capabilities

        ]

        prompt = self._build_prompt(

            message,

            capabilities,

        )

        # --------------------------------------------------

        # Fallback if LLM unavailable

        # --------------------------------------------------

        if self.llm is None:

            capability = self._keyword_router(

                message,

                available_tools,

            )

            return RoutingDecision(

                capability=capability,

                confidence=0.25,

                reason="Keyword fallback.",

            )

        # --------------------------------------------------

        # LLM

        # --------------------------------------------------

        try:

            response = self.llm.invoke(

                prompt

            )

            data = json.loads(

                response.content

            )

            capability = data.get(

                "capability"

            )

            if capability not in available_tools:

                logger.warning(

                    "LLM selected invalid tool '%s'",

                    capability,

                )

                capability = self._keyword_router(

                    message,

                    available_tools,

                )

                return RoutingDecision(

                    capability=capability,

                    confidence=0.30,

                    reason="LLM hallucinated. Keyword fallback."

                )

            return RoutingDecision(

                capability=capability,

                confidence=1.0,

                reason="LLM routing",

            )

        except Exception:

            logger.exception(

                "Router failed"

            )

            capability = self._keyword_router(

                message,

                available_tools,

            )

            return RoutingDecision(

                capability=capability,

                confidence=0.20,

                reason="Exception fallback",

            )

    # ======================================================
    # Prompt
    # ======================================================

    def _build_prompt(

        self,

        message,

        capabilities,

    ):

        capability_prompt = "\n".join(

            [

                f"- {item['name']}: {item['description']}"

                for item in capabilities

            ]

        )

        return f"""
You are an MCP routing agent.

You MUST choose exactly ONE tool.

Never invent tools.

Available MCP Tools

{capability_prompt}

User Request

{message}

Return JSON only.

{{
    "capability":"tool_name"
}}
"""

    # ======================================================
    # Simple Fallback Router
    # ======================================================

    def _keyword_router(

        self,

        message,

        available_tools,

    ):

        message = message.lower()

        mapping = {

            "cancel": "cancel_booking",

            "refund": "process_refund",

            "rebook": "rebook_flight",

            "delay": "get_flight_status",

            "weather": "get_weather",

            "airport": "get_nearby_airports",

            "profile": "get_customer_profile",

        }

        for keyword, tool in mapping.items():

            if (

                keyword in message

                and tool in available_tools

            ):

                return tool

        return None

    # ======================================================
    # Constrained ReAct Validation
    # ======================================================

    async def validate_capability(

        self,

        tool_name: str,

    ) -> bool:

        return await self.registry.has_capability(

            tool_name

        )