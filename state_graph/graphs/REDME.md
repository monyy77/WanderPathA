## Graph 1: Flight Rebooking & Coordination (`state_graph/graphs/flight_rebooking.py`)

### The problem
When a Wanderpath flight is cancelled or delayed, rebooking the
customer isn't something that can run start-to-finish in one pass. It
genuinely depends on things outside our control: how the customer
wants to proceed, and whether the airline can actually confirm an
alternative. This graph models that as explicit states and
transitions instead of a straight-line script.

### Why this needs to be a state graph
- **`awaiting_customer_response`** and **`awaiting_airline_response`**
  are genuine wait states - a reply can take hours, or may never come
  at all. Neither node guesses; each only acts once an outside event
  (the platform recording a customer reply, or a webhook recording the
  airline's response) has written a value into the state.
- **A real cycle**: if the airline rejects a proposed alternative, the
  graph doesn't fail - it logs the rejected attempt and goes back to
  `search_alternatives` to try again. This is the loop that would be
  impossible to represent in a plain DAG.
- **Two HITL points**, each backed by a real constraint:
  - A customer who never replies within the window is **not**
    auto-rebooked - that could conflict with their actual plans, so a
    human agent decides what happens next (`hitl_no_response`).
  - A refund at or above **$500** requires a human agent's approval
    before processing, grounded in Wanderpath's actual refund policy
    (`hitl_refund_approval`) - see the RAG section below for where
    that threshold comes from.

### State shape
```python
{
    "run_id": str,
    "flight_id": int,
    "customer_id": int,
    "customer_is_vip": bool,
    "customer_response": str | None,     # "rebook" | "refund" | None
    "connected_services": list | None,
    "rebooking_plan": list[dict] | None, # from task decomposition
    "alternatives_tried": list[dict],
    "proposed_alternative": dict | None,
    "airline_response": str | None,
    "refund_amount": float | None,
    "refund_decision": dict | None,      # from RAG policy lookup
    "refund_approved": bool | None,
    "final_outcome": str | None,
}
```

### The two LLM-call additions (Issue #3)

**1. Task decomposition** (`task_decomposition.py`) - runs once, the
first time a customer chooses to rebook. Builds the ordered plan
(cancel old booking → search new flight → rebook connected services →
notify customer) and stores it in state so it survives a crash and
resume, instead of being re-derived from scratch.

**2. RAG** (`policy_rag.py`) - grounds the refund decision in
Wanderpath's actual policy documents rather than the model's guess of
"typical" airline policy. The retrieved policy chunk IDs (e.g.
`refund-002`) are stored in `state["refund_decision"]["cited_policy_ids"]`
so an admin reviewing a HITL request can see exactly which policy
backed the calculation.

**Why these two, and not Tree of Thoughts/LATS or constrained ReAct:**
this graph never needs to search over multiple possible plans - the
rebooking sequence is fixed and known in advance, so there's nothing
for ToT/LATS to search over. It also never needs a tool-calling loop
at the decision point itself - the refund/rebooking decisions here are
look-up-and-branch, not act-and-observe, so constrained ReAct doesn't
fit either.

### How resume works
Every node returns `(next_node_name, updated_state)`. The graph runner
saves a checkpoint after every node via `checkpointer.save_checkpoint()`
(see the Checkpointing section above). If a node needs a human or an
external system, the runner stops looping entirely - the process can
exit. Later, `resume_run(run_id)` is called (by the platform after an
admin acts, or by a webhook handler after the airline responds), and
it reads the last checkpoint and continues from exactly that node -
it does not restart from the top.

### Setup
No extra dependencies beyond what Issue #1 already requires
(`mysql-connector-python`, `python-dotenv`) - this graph reuses the
same checkpointer.

### How to verify it works
```bash
python state_graph/graphs/test_flight_rebooking.py
```
This runs 5 end-to-end scenarios against the live checkpointer:
1. A refund under $500 - auto-approved, no HITL.
2. A refund at/above $500 - pauses at HITL, resumes correctly after a
   simulated admin approval.
3. A rebooking where the airline rejects the first alternative,
   proving the cycle actually re-enters `search_alternatives` and
   succeeds on the second attempt.
4. A customer who never replies - proving the graph escalates to a
   human instead of silently rebooking them.
5. Prints a fresh `run_id` with instructions to manually kill the
   process and confirm the checkpoint survives (crash-and-resume
   proof, same principle as Issue #1's manual test).

All 5 scenarios pass against the live MySQL checkpointer.