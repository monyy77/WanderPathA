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
        message: str,
        available_tools: list[str],
    ) -> Optional[str]:

        message = message.lower()

        mapping = [
            (
                [
                    "refund",
                    "refund money",
                    "money back",
                    "reimbursement",
                    "eligible for refund",
                ],
                "check_refund_eligibility",
            ),
            (
                [
                    "compensation",
                    "compensate",
                ],
                "calculate_compensation",
            ),
            (
                [
                    "flight status",
                    "flight delayed",
                    "delay",
                    "delayed",
                    "cancelled",
                    "canceled",
                ],
                "get_flight_status",
            ),
            (
                ["weather"],
                "get_weather",
            ),
            (
                [
                    "airport",
                    "nearby airport",
                ],
                "get_nearby_airports",
            ),
            (
                [
                    "profile",
                    "customer profile",
                    "my information",
                ],
                "get_customer_profile",
            ),
            (
                [
                    "booking history",
                    "past bookings",
                    "my bookings",
                ],
                "get_booking_history",
            ),
            (
                [
                    "delay duration",
                    "how long is the delay",
                ],
                "get_delay_duration",
            ),
            (
                [
                    "connection risk",
                    "miss my connection",
                ],
                "check_connection_risk",
            ),
        ]

        for keywords, tool_name in mapping:
            if tool_name in available_tools:
                if any(keyword in message for keyword in keywords):
                    return tool_name

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