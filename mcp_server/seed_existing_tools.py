"""
server/seed_existing_tools.py

One-time seed script for Issue #5.
Owner: Person 1

WHY THIS SCRIPT EXISTS:
server.py now wraps every tool with guarded()/guarded_async_decorator(),
which checks RegisteredTools before allowing a call. Any tool NOT
already present in that table would be rejected as "not registered" -
even though it's a real, working tool that existed before this issue.
This script registers all the tools server.py already wires up, with
is_active=True, so nothing breaks: the system keeps working exactly as
before, and an admin can now choose to deregister any of them going
forward.

Run once:
    python server/seed_existing_tools.py

Safe to run more than once - register_tool() reactivates/updates an
existing row by tool_name rather than creating duplicates (see
server/tool_registry.py).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_server.tool_registry import register_tool

# One entry per tool currently wired into server.py via guarded(...) or
# guarded_async_decorator(...). agent_name/description/parameters_schema
# are kept simple here since the goal is registering what already
# exists, not redesigning each tool's interface.
EXISTING_TOOLS = [
    {
        "tool_name": "get_flight_status",
        "agent_name": "travel_status",
        "description": "Get the current status of a flight.",
        "parameters_schema": {"flight_id": "int"},
    },
    {
        "tool_name": "get_weather",
        "agent_name": "travel_status",
        "description": "Get current weather at an airport.",
        "parameters_schema": {"airport_code": "string"},
    },
    {
        "tool_name": "get_delay_duration",
        "agent_name": "travel_status",
        "description": "Get how long a flight has been delayed.",
        "parameters_schema": {"flight_id": "int"},
    },
    {
        "tool_name": "check_disruption_reason",
        "agent_name": "travel_status",
        "description": "Check the reason a flight was disrupted.",
        "parameters_schema": {"flight_id": "int"},
    },
    {
        "tool_name": "get_nearby_airports",
        "agent_name": "booking",
        "description": "Find airports near a given location.",
        "parameters_schema": {"location": "string"},
    },
    {
        "tool_name": "get_flight_options",
        "agent_name": "booking",
        "description": "Search for available flight options.",
        "parameters_schema": {"origin": "string", "destination": "string"},
    },
    {
        "tool_name": "get_customer_profile",
        "agent_name": "customer",
        "description": "Fetch a customer's profile information.",
        "parameters_schema": {"customer_id": "int"},
    },
    {
        "tool_name": "get_booking_history",
        "agent_name": "customer",
        "description": "Fetch a customer's past booking history.",
        "parameters_schema": {"customer_id": "int"},
    },
    {
        "tool_name": "get_bookings_by_flight",
        "agent_name": "flight_rebooking",
        "description": "Get all bookings/customers on a disrupted flight.",
        "parameters_schema": {"flight_id": "int"},
    },
    {
        "tool_name": "check_connection_risk",
        "agent_name": "flight_rebooking",
        "description": "Check whether a delay puts a connection at risk.",
        "parameters_schema": {"flight_id": "int"},
    },
    {
        "tool_name": "get_disruption_severity",
        "agent_name": "flight_rebooking",
        "description": "Assess how severe a flight disruption is.",
        "parameters_schema": {"flight_id": "int"},
    },
    {
        "tool_name": "check_alternative_transport",
        "agent_name": "flight_rebooking",
        "description": "Check alternative transport options for a destination.",
        "parameters_schema": {"destination_airport": "string"},
    },
    {
        "tool_name": "CalculateCompensation",
        "agent_name": "flight_rebooking",
        "description": "Calculate compensation owed for a disruption.",
        "parameters_schema": {"booking_id": "int"},
    },
    {
        "tool_name": "escalate_to_human",
        "agent_name": "flight_rebooking",
        "description": "Escalate a case to a human agent (HITL).",
        "parameters_schema": {"booking_id": "int", "reason": "string"},
    },
    {
        "tool_name": "upgrade_to_vip",
        "agent_name": "customer",
        "description": "Upgrade a customer to VIP status, unlocking VIP-only tools.",
        "parameters_schema": {"customer_id": "int"},
    },
]


def seed():
    print(f"Seeding {len(EXISTING_TOOLS)} existing tools into RegisteredTools...\n")
    for tool_def in EXISTING_TOOLS:
        tool_id = register_tool(tool_def)
        print(f"  Registered '{tool_def['tool_name']}' (tool_id={tool_id}, active=True)")
    print("\nDone. All existing tools are registered and active.")


if __name__ == "__main__":
    seed()