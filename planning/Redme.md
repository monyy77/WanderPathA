# Planning Agent -- IROPS Reshuffle

## Owner (this doc's scope): Person 1 -- Planning Layer

A **new** agent, separate from the existing Memory/RAG agent (`agent/agent.py`),
reusing the same MCP server (`server/server.py`) and database (`db/`).

## The real recurring request

> "Flight X has been disrupted (cancelled, or delayed past a real threshold).
> Reshuffle every booking affected by it."

This is real inside WanderPathA's own schema: `Flights.status/delay_minutes/
disruption_reason/connection_risk/severity`, `AlternativeTransport`,
`Bookings.refund_eligible/compensation`, and `Escalations` all exist
specifically to support this workflow -- it isn't an invented scenario.

It qualifies as a genuine planning problem, not a memory/RAG problem:

- **Real ambiguity**: which bookings are actually affected, and in what
  order, depends on connection risk, VIP status, and disruption severity --
  not a fixed lookup.
- **Real branching**: several valid rebooking proposals usually exist per
  customer (different flights, alternative transport, vouchers).
- **Real cost of a wrong plan**: a bad proposal can strand a VIP connection
  or offer a rebooking option that turns out to have no seats.
- **Real mid-plan surprises**: alternative-flight availability, weather, and
  airport status are only known once queried -- a plan made without that
  information can go stale mid-execution.

## Files (this concern)

| File | What it is |
|---|---|
| `dag.py` | Forked from the toolkit's `models.py`. `Task`/`Plan` pydantic models; acyclicity enforced at construction time (`Plan.validate_dag`), not as a runtime check. Added `TaskType` (`tool_call` / `reasoning` / `planned`) so a node can dispatch to a real MCP tool, not just an LLM call. |
| `decomposition.py` | Forked from `algorithms/decomposition.py`. **Decomposition-first**: whole DAG generated in one call, then executed in topological, dependency-safe batches (parallel within a batch via `asyncio.gather`). `TOOL_CALL` nodes hit real MCP tools; `PLANNED` nodes are handed to `planner_router` (Person 2). |
| `dynamic_decomposition.py` | Forked from `algorithms/dynamic_decomposition.py`. **Dynamic/interleaved**: next step chosen only after observing the last tool result, so a live surprise (e.g. zero alternative flights) can change the plan mid-run instead of executing a stale one. |
| `planner_router.py` | Interface + fallback only. Real PS/ToT/LATS routing is Person 2's `planner_selector.py` -- this file defines the contract `decomposition.py`/`dynamic_decomposition.py` call into. |
| `planning_agent.py` | Entry point. Wires goal -> mode (`decomposition_first` / `dynamic`) -> execution -> JSON trace in `artifacts/` (toolkit's trace convention, extended with latency/call counts, no second logging system). |

## MCP server changes

Several tools already existed in `tools/*.py` but weren't registered on
`server/server.py`: `check_connection_risk`, `get_disruption_severity`,
`check_alternative_transport`, `CalculateCompensation`,
`escalate_to_human`. Registered, not rebuilt.

One genuinely new, narrow tool was added: `get_bookings_by_flight(flight_id)`
in `tools/booking_tools.py` -- nothing previously answered "which bookings
are on this disrupted flight" (the existing `get_booking_history` only
filters by customer).

## Decomposition-first DAG (7 nodes, ships as the default for simple cases)

```
t1 gather_disruption_info   (tool_call, no deps)
t2 gather_affected_bookings (tool_call, no deps)
t3 assess_priority          (reasoning, depends: t1, t2)
t4 find_alternatives        (tool_call, depends: t1)
t5 propose_rebooking_plan   (planned -> PS/ToT/LATS, depends: t3, t4)
t6 calculate_compensation   (tool_call, depends: t1, t3)
t7 synthesize_final_plan    (reasoning, terminal, depends: t5, t6)
```

## Where decomposition-first and dynamic genuinely diverge

- **Favors dynamic**: a disrupted flight whose alternative-flight lookup
  (`t4`) comes back empty. Decomposition-first already committed to a
  rebooking-proposal node assuming alternatives exist; dynamic decomposition
  only learns this live and reroutes to alternative transport / escalation
  instead of executing a plan built on a false assumption.
- **Favors decomposition-first**: a simple 2-6 hour delay, one non-VIP
  booking, no connection risk -- no real branching, so the fixed upfront
  plan is just as accurate and cheaper (fewer LLM calls) than replanning
  step by step.

Both cases are part of the fixed test suite in `planning_eval/` (Person 3),
run against both modes to produce the comparison table.

## Not this file's concern

- Which of PS/ToT/LATS a `planned` node actually routes to, and why --
  `planner_router.py`/`planner_selector.py` (Person 2).
- Self-Refine / Reflexion / grounded environment -- `execution/` (Person 3).
- The comparison table and test suite -- `planning_eval/` (Person 3).
