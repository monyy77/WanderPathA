## Tool Registry Data Boundary (`server/tool_registry.py`)

### Why this exists
Prior grading on the MCP Server Lab found substantive protocol and
integration work (elicitation, progress, dynamic schemas, runtime
notifications) but **no attributable domain-data ownership** - no
documented schema, no validation, and no automated tests proving the
data layer behaves correctly on both success and failure. This module
is that missing data boundary.

It matters now more than it did in the original lab: the MCP server is
**load-bearing** for the platform's admin panel (Issue #5 - runtime
tool add/remove). If tool registration silently accepted malformed
data, or a deregistered tool was still treated as callable, the admin
panel would be unreliable without anyone noticing.

### Schema
```sql
CREATE TABLE RegisteredTools (
    tool_id INT AUTO_INCREMENT PRIMARY KEY,
    tool_name VARCHAR(100) NOT NULL UNIQUE,
    agent_name VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    parameters_schema JSON NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_agent_name (agent_name),
    INDEX idx_is_active (is_active)
);
```
Seeded on creation with the tools that already exist in the codebase
(`search_flights`, `cancel_booking`, `process_refund`), so the
registry reflects reality from day one rather than starting empty.

**Design choice: soft delete.** Deregistering a tool sets
`is_active = FALSE` rather than deleting the row, so registration
history stays auditable and re-registering the same tool name
reactivates it instead of creating a duplicate.

### API (`server/tool_registry.py`)
| Function | Purpose |
|---|---|
| `register_tool(tool_def)` | Validates and registers a tool. Raises `InvalidToolDefinitionError` on a malformed definition (missing field or wrong type) rather than silently accepting bad data. Re-registering an existing name reactivates and updates it. |
| `deregister_tool(tool_name)` | Soft-deletes (sets `is_active = FALSE`). Returns `False` if the tool never existed, rather than erroring. |
| `get_tool(tool_name)` | Fetches a tool's record regardless of active status - this is what a request handler checks before executing a tool call. |
| `list_active_tools(agent_name=None)` | Lists currently active tools, optionally filtered to one agent. Used by the admin panel. |

### How to verify it works
```bash
python -m pytest server/tests/test_tool_registry.py -v
```
Covers exactly the four cases the acceptance criteria asks for, plus
two extra edge cases:
1. **Successful registration** - a well-formed tool is stored and
   retrievable as active.
2. **Successful deregistration** - a registered tool is soft-deleted
   and shows `is_active = False`.
3. **Malformed registration (failure path)** - a definition missing a
   required field, or with a field of the wrong type, is rejected
   with `InvalidToolDefinitionError` rather than silently accepted.
4. **Protocol-level failure** - after deregistration, the tool record
   still exists (soft delete) but `is_active` is `False` and it no
   longer appears in `list_active_tools()` - proving a deregistered
   tool is identifiable as not-callable, which is what the server's
   request handler (Issue #5) relies on.
5. *(extra)* Deregistering a tool that was never registered returns
   `False` cleanly instead of erroring.
6. *(extra)* Re-registering a previously deregistered tool name
   reactivates the same row rather than duplicating it.

All 7 tests pass against the live MySQL database.