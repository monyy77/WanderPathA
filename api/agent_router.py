from typing import Any

class AgentRouter:
    async def route(
        self,
        agent_id: str,
        message: str,
        session_id: str,
        customer_id: str | None = None,
    ) -> dict:

        if agent_id == "planning":
            return await self._planning(message)

        elif agent_id == "memory":
            return await self._memory(message, customer_id)

        elif agent_id == "flight":
            return await self._flight(message)

        elif agent_id == "refund":
            return await self._refund(message)

        elif agent_id == "vip":
            return await self._vip(message)

        raise ValueError(f"Unknown agent: {agent_id}")

    async def _planning(self, message: str) -> dict:
        raise NotImplementedError

    async def _memory(self, message: str, customer_id: str | None) -> dict:
        raise NotImplementedError

    async def _flight(self, message: str) -> dict:
        raise NotImplementedError

    async def _refund(self, message: str) -> dict:
        raise NotImplementedError

    async def _vip(self, message: str) -> dict:
        raise NotImplementedError
