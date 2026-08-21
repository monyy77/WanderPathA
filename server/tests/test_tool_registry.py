"""
mcp_server/tests/test_tool_registry.py

Automated tests for the tool registry (Issue #4).
Owner: Person 1

Run with:
    pytest mcp_server/tests/test_tool_registry.py -v

Covers exactly the four cases the acceptance criteria asks for:
  1. Successful tool registration.
  2. Successful deregistration.
  3. A malformed/invalid registration attempt (failure path).
  4. A protocol-level failure: a client requesting a deregistered
     tool must be identifiable as inactive, not silently treated as
     if it were still callable.
"""

import sys
import os
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from server.tool_registry import (
    register_tool,
    deregister_tool,
    get_tool,
    list_active_tools,
    InvalidToolDefinitionError,
)


def _unique_tool_name(prefix: str) -> str:
    """Generates a unique tool name per test run so repeated test runs
    don't collide with leftover data from a previous run."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_successful_tool_registration():
    """A well-formed tool definition should register successfully and
    be retrievable and marked active."""
    tool_name = _unique_tool_name("test_tool")
    tool_def = {
        "tool_name": tool_name,
        "agent_name": "flight_rebooking",
        "description": "A test tool for registration.",
        "parameters_schema": {"flight_id": "int"},
    }

    tool_id = register_tool(tool_def)
    assert isinstance(tool_id, int)

    stored = get_tool(tool_name)
    assert stored is not None
    assert stored["tool_name"] == tool_name
    assert stored["agent_name"] == "flight_rebooking"
    assert stored["is_active"] is True
    assert stored["parameters_schema"] == {"flight_id": "int"}


def test_successful_deregistration():
    """A registered tool should be deregistered successfully, and
    should then show as inactive rather than disappearing entirely
    (soft delete, so the record is auditable)."""
    tool_name = _unique_tool_name("test_tool_deregister")
    register_tool(
        {
            "tool_name": tool_name,
            "agent_name": "flight_rebooking",
            "description": "A test tool to be deregistered.",
            "parameters_schema": {},
        }
    )

    was_deregistered = deregister_tool(tool_name)
    assert was_deregistered is True

    stored = get_tool(tool_name)
    assert stored is not None
    assert stored["is_active"] is False


def test_deregistering_nonexistent_tool_returns_false():
    """Deregistering a tool that was never registered should not
    error - it should clearly report that nothing happened."""
    result = deregister_tool("this_tool_was_never_registered_xyz")
    assert result is False


def test_malformed_registration_missing_field_fails():
    """FAILURE PATH: a tool definition missing a required field must
    be rejected loudly (InvalidToolDefinitionError), not silently
    accepted with a null/default field."""
    incomplete_def = {
        "tool_name": _unique_tool_name("bad_tool"),
        "agent_name": "flight_rebooking",
        # "description" and "parameters_schema" are missing on purpose.
    }
    with pytest.raises(InvalidToolDefinitionError):
        register_tool(incomplete_def)


def test_malformed_registration_wrong_type_fails():
    """FAILURE PATH: parameters_schema must be a dict. A string (or
    any other wrong type) must be rejected, not coerced or ignored."""
    bad_def = {
        "tool_name": _unique_tool_name("bad_type_tool"),
        "agent_name": "flight_rebooking",
        "description": "A tool with a broken schema field.",
        "parameters_schema": "this should be a dict, not a string",
    }
    with pytest.raises(InvalidToolDefinitionError):
        register_tool(bad_def)


def test_protocol_level_failure_deregistered_tool_is_not_callable():
    """
    PROTOCOL-LEVEL FAILURE PATH: after a tool is deregistered, any
    code path that checks "is this tool currently callable?" must see
    is_active == False. This is what the MCP server's request handler
    (Issue #5) checks before executing a tool call - a request for a
    deregistered tool must be rejected, not silently executed.
    """
    tool_name = _unique_tool_name("protocol_test_tool")
    register_tool(
        {
            "tool_name": tool_name,
            "agent_name": "flight_rebooking",
            "description": "A tool to test protocol-level rejection.",
            "parameters_schema": {},
        }
    )
    deregister_tool(tool_name)

    # Simulate what the server's request handler would check before
    # allowing a tool call to execute.
    tool = get_tool(tool_name)
    assert tool is not None, "The tool record should still exist (soft delete)"
    is_callable = tool["is_active"]
    assert is_callable is False, (
        "A deregistered tool must NOT be treated as callable - this is "
        "the protocol-level failure the server must guard against."
    )

    # It should also not appear in the list of active tools.
    active_tools = list_active_tools(agent_name="flight_rebooking")
    active_names = [t["tool_name"] for t in active_tools]
    assert tool_name not in active_names


def test_reregistering_existing_tool_reactivates_it():
    """Registering a tool with the same name as a previously
    deregistered one should reactivate it (update in place) rather
    than creating a duplicate row - tool_name is unique."""
    tool_name = _unique_tool_name("reregister_tool")
    tool_def = {
        "tool_name": tool_name,
        "agent_name": "flight_rebooking",
        "description": "Original description.",
        "parameters_schema": {"a": "int"},
    }
    first_id = register_tool(tool_def)
    deregister_tool(tool_name)

    updated_def = {**tool_def, "description": "Updated description."}
    second_id = register_tool(updated_def)

    assert first_id == second_id, "Re-registering should reuse the same tool_id"
    stored = get_tool(tool_name)
    assert stored["is_active"] is True
    assert stored["description"] == "Updated description."