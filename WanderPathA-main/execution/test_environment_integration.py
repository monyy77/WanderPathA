import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from planning.environment import TravelEnvironment


class FakeToolResult:
    """محاكاة لمخرجات أدوات MCP المتوقعة من الـ Environment"""
    def __init__(self):
        self.structured_content = {
            "success": True,
            "flight_id": 55,
            "available_seats": 3,
        }
        self.content = "Flight 55 is available."


class FakeTool:
    async def ainvoke(self, args):
        return FakeToolResult()


@pytest.mark.asyncio
async def test_environment_with_mcp_tool():
    tools = {
        "get_flight_options": FakeTool()
    }

    environment = TravelEnvironment(
        mcp_tools=tools,
        validator_tool="get_flight_options"
    )

    feedback = await environment.evaluate(
        candidate="Rebook passenger to flight 55",
        task="Choose an alternative flight"
    )

    assert feedback.success is True
    assert feedback.score > 0

    