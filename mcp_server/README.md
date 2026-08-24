# Transport Configuration

## STDIO (Default)

- Used for direct process-to-process communication
- Suitable for: Testing, local development, single machine
- Justification: Simpler to test, no network overhead

## HTTP (Alternative)

- Streamable HTTP at localhost:8000/mcp
- Suitable for: Remote access, multiple clients

# Runtime Tool Management (Issue #5)

## The problem
Before this, adding or removing a tool from an agent required editing
`server/server.py` and redeploying the whole MCP server - an admin had
no way to control what a live agent could call without engineering
involvement.

## How it works now

### 1. A live data boundary (Issue #4)
`server/tool_registry.py` provides a validated, tested CRUD layer over
the `RegisteredTools` table: `register_tool()`, `deregister_tool()`,
`get_tool()`, `list_active_tools()`. This is the single source of
truth for "is this tool currently allowed to run."

### 2. A runtime guard on every tool call (`server/tool_guard.py`)
`mcp.tool()` (from FastMCP) registers each tool once, when the server
process starts - it has no concept of "this tool was deregistered by
an admin five minutes ago." Re-deploying the server every time an
admin toggles a tool would fail the requirement that this be
near-runtime, not hand-edit-and-redeploy.

Instead, every tool in `server.py` is wrapped with `guarded(...)` (for
plain sync functions) or `@guarded_async_decorator(...)` (for `async
def` tools like `upgrade_to_vip`). The wrapper checks
`RegisteredTools.is_active` **immediately before** the tool's actual
logic runs - on every single call, not just at startup. This is what
makes an admin's deregister action reach the live server: the guard
always reads the live table, so behavior changes the moment the row
changes, regardless of which process wrote it.

```python
# Before:
mcp.tool()(check_connection_risk.func)

# After:
mcp.tool()(guarded("check_connection_risk", check_connection_risk.func))
```

If a deregistered (or never-registered) tool is called, the guard
raises `ToolNotActiveError` instead of running the underlying
function.

### 3. A real admin API (`server/admin_tools_api.py`)
FastAPI endpoints the admin panel calls - not a mock:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/admin/tools/` | List active tools (optionally filtered by `agent_name`) |
| POST | `/admin/tools/register` | Register or reactivate a tool |
| POST | `/admin/tools/deregister` | Deregister a tool by name |
| GET | `/admin/tools/{tool_name}` | Get a single tool's record, active or not |

A malformed registration request returns `400` (via
`InvalidToolDefinitionError` from Issue #4); deregistering a
never-registered tool returns `404`.

### 4. Seeding existing tools (`server/seed_existing_tools.py`)
Once the guard was added, every tool already wired into `server.py`
needed a row in `RegisteredTools` (as active), or the guard would
reject them all as "not registered." This one-time script seeds all
15 existing tools. Safe to re-run - `register_tool()` reactivates an
existing row by name rather than duplicating it.

Run once:
```bash
python server/seed_existing_tools.py
```

## How to verify a tool change actually reaches the live server

This is the core acceptance criterion: a UI toggle that doesn't change
what the agent can call earns no credit. To verify manually:

1. Start the server: `python -m server.server stdio`
2. Confirm a tool works normally (e.g. call `check_connection_risk`).
3. Deregister it via the admin API:
   ```bash
   curl -X POST http://localhost:8000/admin/tools/deregister \
        -H "Content-Type: application/json" \
        -d '{"tool_name": "check_connection_risk"}'
   ```
   (or directly: `from server.tool_registry import deregister_tool;
   deregister_tool("check_connection_risk")`)
4. Immediately attempt to call `check_connection_risk` again through
   the running server - **no restart in between**. It is rejected with
   `ToolNotActiveError`, proving the change reached the live process
   without a redeploy.
5. Re-register it the same way and confirm it becomes callable again.

## Files in this issue
- `server/tool_guard.py` - the runtime enforcement wrapper (sync + async).
- `server/admin_tools_api.py` - the FastAPI endpoints for the admin panel.
- `server/seed_existing_tools.py` - one-time seed for pre-existing tools.
- `server/tool_registry.py` - the data layer this all depends on (Issue #4).

## Dependency on Issue #4
This issue builds directly on the data-boundary and validation work
from Issue #4 - `register_tool()`'s validation
(`InvalidToolDefinitionError`) and the `is_active` soft-delete design
are what make both the guard and the admin API safe to build on.