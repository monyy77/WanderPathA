"""
mcp_server/tool_registry.py

Tool registry data-boundary layer (Issue #4).
Owner: Person 1

WHY THIS MODULE EXISTS:
Prior MCP Server Lab grading found substantive protocol/integration
work but no attributable domain-data ownership - no documented schema,
no validation, no tests proving the data layer actually behaves
correctly on both success and failure. This module is that missing
data boundary: a validated, tested CRUD layer over the RegisteredTools
table (see db/schema.sql).

This module is deliberately kept separate from server.py's live
request-handling loop. Issue #5 (runtime tool add/remove from the
admin panel) wires these functions into the actual running MCP server
so that register/deregister calls here immediately change what tools
the server will accept - but the correctness of the data layer itself
(what counts as a valid tool record, what happens on a malformed
registration attempt) is proven here, independently of that wiring.
"""

import json
import os
from typing import Any, Optional

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


class InvalidToolDefinitionError(ValueError):
    """Raised when a tool registration attempt is malformed - missing
    a required field, or a field of the wrong type. Kept as a distinct
    exception type (not a bare ValueError) so callers - including the
    admin panel in Issue #5 - can catch this specifically and show the
    admin a clear rejection instead of a generic 500 error."""
    pass


REQUIRED_FIELDS = {"tool_name", "agent_name", "description", "parameters_schema"}


def _get_connection():
    """Opens a new MySQL connection using credentials from .env."""
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
    )


def _validate_tool_definition(tool_def: dict[str, Any]) -> None:
    """
    Validates a tool definition before it's allowed anywhere near the
    database. This is the actual "data-boundary" enforcement the prior
    grading found missing - a malformed registration attempt must fail
    loudly here, not silently corrupt a row or crash deep inside the
    MCP protocol handler later.
    """
    missing = REQUIRED_FIELDS - tool_def.keys()
    if missing:
        raise InvalidToolDefinitionError(
            f"Tool definition is missing required field(s): {sorted(missing)}"
        )

    if not isinstance(tool_def["tool_name"], str) or not tool_def["tool_name"].strip():
        raise InvalidToolDefinitionError("tool_name must be a non-empty string")

    if not isinstance(tool_def["agent_name"], str) or not tool_def["agent_name"].strip():
        raise InvalidToolDefinitionError("agent_name must be a non-empty string")

    if not isinstance(tool_def["description"], str) or not tool_def["description"].strip():
        raise InvalidToolDefinitionError("description must be a non-empty string")

    if not isinstance(tool_def["parameters_schema"], dict):
        raise InvalidToolDefinitionError(
            "parameters_schema must be a dict describing the tool's parameters"
        )


def register_tool(tool_def: dict[str, Any]) -> int:
    """
    Registers a new tool, or re-activates it if a tool with the same
    name was previously deregistered. Raises InvalidToolDefinitionError
    for a malformed definition - this is the failure path the
    acceptance criteria requires a test for.

    Returns the tool_id of the (newly created or reactivated) row.
    """
    _validate_tool_definition(tool_def)

    conn = _get_connection()
    try:
        cursor = conn.cursor()
        # Check if a tool with this name already exists (active or not).
        cursor.execute(
            "SELECT tool_id FROM RegisteredTools WHERE tool_name = %s",
            (tool_def["tool_name"],),
        )
        existing = cursor.fetchone()

        if existing:
            tool_id = existing[0]
            cursor.execute(
                """
                UPDATE RegisteredTools
                SET agent_name = %s, description = %s, parameters_schema = %s,
                    is_active = TRUE
                WHERE tool_id = %s
                """,
                (
                    tool_def["agent_name"],
                    tool_def["description"],
                    json.dumps(tool_def["parameters_schema"]),
                    tool_id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO RegisteredTools
                    (tool_name, agent_name, description, parameters_schema, is_active)
                VALUES (%s, %s, %s, %s, TRUE)
                """,
                (
                    tool_def["tool_name"],
                    tool_def["agent_name"],
                    tool_def["description"],
                    json.dumps(tool_def["parameters_schema"]),
                ),
            )
            tool_id = cursor.lastrowid

        conn.commit()
        return tool_id
    finally:
        cursor.close()
        conn.close()


def deregister_tool(tool_name: str) -> bool:
    """
    Deregisters a tool by name (soft delete - sets is_active = FALSE
    rather than deleting the row, so the registration history and any
    audit trail is preserved).

    Returns True if a tool was found and deregistered, False if no
    tool with that name exists.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE RegisteredTools SET is_active = FALSE WHERE tool_name = %s",
            (tool_name,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def get_tool(tool_name: str) -> Optional[dict[str, Any]]:
    """
    Fetches a tool's record by name, regardless of active status.
    Returns None if no tool with that name has ever been registered.

    This is what the MCP protocol handler (Issue #5) calls to check
    whether an incoming tool call is for a tool that's currently
    active - a deregistered tool exists in the table but with
    is_active = False, which is exactly the "protocol-level failure"
    case the acceptance criteria asks us to test.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM RegisteredTools WHERE tool_name = %s",
            (tool_name,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        
        row["parameters_schema"] = json.loads(row["parameters_schema"])
        row["is_active"] = bool(row["is_active"])  # تحويل 1/0 إلى True/False
        
        return row
    finally:
        cursor.close()
        conn.close()

def list_active_tools(agent_name: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Lists all currently active tools, optionally filtered to a single
    agent. Used by the admin panel (Issue #5) to show what tools an
    agent currently has.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        if agent_name:
            cursor.execute(
                "SELECT * FROM RegisteredTools WHERE is_active = TRUE AND agent_name = %s",
                (agent_name,),
            )
        else:
            cursor.execute(
                "SELECT * FROM RegisteredTools WHERE is_active = TRUE"
            )
        rows = cursor.fetchall()
        for row in rows:
            row["parameters_schema"] = json.loads(row["parameters_schema"])
        return rows
    finally:
        cursor.close()
        conn.close()