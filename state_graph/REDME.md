## State Graph Checkpointing (`state_graph/`)

### Why this exists
Our state graphs (starting with the flight-rebooking graph) can pause for
real reasons — waiting on an airline's response can take hours. If the
server process restarts while a run is paused, we can't afford to lose
what's already been decided or re-run steps that already completed. This
layer persists the full state of a graph run to MySQL after every
meaningful transition, so a run can be killed and resumed from exactly
where it left off.

### Design
- **Append-only log**: every `save_checkpoint()` call inserts a new row
  into `GraphCheckpoints` rather than overwriting the previous one.
  `load_checkpoint()` returns the most recent row for a given `run_id`.
  This gives us a full audit trail of every transition a run went
  through, which is also what we use as evidence for the crash-and-resume
  demo.
- **Storage**: MySQL table `GraphCheckpoints` (see `db/schema.sql`), with
  the state itself stored as a `JSON` column (`state_json`).

### Schema
```sql
CREATE TABLE GraphCheckpoints (
    checkpoint_id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(100) NOT NULL,
    graph_name VARCHAR(100) NOT NULL,
    current_node VARCHAR(100) NOT NULL,
    state_json JSON NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_run_id (run_id),
    INDEX idx_run_id_created (run_id, created_at)
);
```

### API (`state_graph/checkpointer.py`)
| Function | Purpose |
|---|---|
| `save_checkpoint(run_id, graph_name, current_node, state, status)` | Persists the graph's full state after a transition. Returns the new `checkpoint_id`. |
| `load_checkpoint(run_id)` | Returns the most recent checkpoint for a run, or `None` if the run doesn't exist. |
| `load_history(run_id)` | Returns every checkpoint for a run, oldest first — used for demo evidence and debugging. |

### Setup
1. Make sure `.env` has `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
   pointing at a MySQL server that has run `db/schema.sql`.
2. Install the dependency (already in `requirements.txt`):
   ```
   pip install -r requirements.txt
   ```

### How to verify it works
```bash
cd state_graph
python test_checkpointer.py
```
This script saves two checkpoints for a throwaway `run_id`, loads the
latest one back and checks it matches, loads the full history and checks
both checkpoints are there in order, and confirms a non-existent
`run_id` correctly returns `None`. All output prints to the console —
no test framework required to read the result.

### How to verify crash-and-resume manually
1. Run `test_checkpointer.py` but comment out Step 2 temporarily.
2. Note the `run_id` it prints.
3. Kill the process (Ctrl+C) right after Step 1 finishes.
4. In a fresh Python session, call `load_checkpoint(run_id)` with that
   same `run_id` and confirm it returns the `"start"` node's state —
   proving the checkpoint survived the process being killed.

*(This same principle is what we'll demonstrate on a full graph run —
not just this isolated test — for the project's final demo evidence.)*