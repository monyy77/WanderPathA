"""
server/tool_guard.py

Runtime enforcement of tool registration status (Issue #5).
Owner: Person 1

WHY THIS FILE EXISTS:
mcp.tool() (see server.py) registers each tool once, when the server
process starts up - it has no built-in concept of "this tool was
deregistered by an admin five minutes ago." Re-deploying the server
every time an admin toggles a tool would fail the acceptance
criteria ("hand-edit + redeploy is not" acceptable).

Instead, this module wraps every tool function with a guard that
checks the live RegisteredTools table (server/tool_registry.py)
immediately before the tool's actual logic runs. This means a tool
deregistered through the admin panel becomes uncallable on the very
next request - the server process itself never needs to restart, and
the change is real, not cosmetic. This is also what makes it
irrelevant which process wrote the deregistration (the admin API in
admin_tools_api.py can run as its own small service) - the guard
always reads the live table, so the live MCP server's actual behavior
changes the moment the row changes, regardless of who wrote it.
"""

import functools
from typing import Any, Callable

from mcp_server.tool_registry import get_tool


class ToolNotActiveError(Exception):
    """
    Raised when a tool call comes in for a tool that is not currently
    active - either it was deregistered by an admin, or it was never
    registered in RegisteredTools at all. The MCP protocol layer
    should turn this into whatever rejection response the client
    expects, rather than silently running the underlying function.
    """
    pass


def _check_active(tool_name: str) -> None:
    """Shared check used by both the sync and async guards."""
    tool_record = get_tool(tool_name)

    if tool_record is None:
        raise ToolNotActiveError(
            f"Tool '{tool_name}' is not registered. It cannot be called."
        )

    if not tool_record["is_active"]:
        raise ToolNotActiveError(
            f"Tool '{tool_name}' has been deregistered by an admin "
            f"and is no longer callable."
        )


def guarded(tool_name: str, tool_func: Callable) -> Callable:
    """
    Wraps a SYNCHRONOUS tool function so every call first checks the
    live registry.

    Usage in server.py (replacing a bare registration):
        mcp.tool()(guarded("check_connection_risk", check_connection_risk.func))
    instead of:
        mcp.tool()(check_connection_risk.func)
    """

    @functools.wraps(tool_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _check_active(tool_name)
        return tool_func(*args, **kwargs)

    return wrapper


def guarded_async(tool_name: str, tool_func: Callable) -> Callable:
    """
    Wraps an ASYNCHRONOUS tool function (e.g. tools defined with
    `async def` taking a Context, like upgrade_to_vip or
    refund_with_confirmation) so every call first checks the live
    registry, exactly like guarded() does for sync functions.

    Usage as a decorator, replacing:
        @mcp.tool()
        async def upgrade_to_vip(ctx: Context, customer_id: int):
            ...
    with:
        @mcp.tool()
        @guarded_async_decorator("upgrade_to_vip")
        async def upgrade_to_vip(ctx: Context, customer_id: int):
            ...
    """

    @functools.wraps(tool_func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        _check_active(tool_name)
        return await tool_func(*args, **kwargs)

    return wrapper


def guarded_async_decorator(tool_name: str) -> Callable:
    """Decorator form of guarded_async, for tools defined inline with
    `@mcp.tool()` + `async def` rather than registered via `.func`."""

    def decorator(tool_func: Callable) -> Callable:
        return guarded_async(tool_name, tool_func)

    return decorator