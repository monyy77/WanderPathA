# WanderPathA – Autonomous Travel Agent System

An MCP-based AI travel assistant with planning, reasoning, memory, retrieval-augmented generation, and grounded tool execution — built for the WanderPath Travel Agency.

## Project Overview

WanderPathA is an autonomous travel agency assistant that handles flight disruptions, cancellations, refunds, rebooking, and general customer support requests through a Model Context Protocol (MCP) architecture.

Rather than a single flat LLM call, the system combines several cooperating layers:

- **Autonomous Agent** — orchestrates the full request lifecycle.
- **MCP Architecture** — a real MCP server exposing deterministic tools over the live database, so the model never touches the database directly.
- **Planning** — decomposes complex requests into a mix of tool calls, reasoning steps, and deliberate multi-path decisions (Plan-and-Solve, Tree of Thoughts, LATS).
- **Memory** — short-term (transcript + scratchpad), episodic, and semantic memory so customer context survives across turns instead of being lost to context pruning.
- **RAG** — retrieval over company policy documents (refunds, cancellations, VIP benefits, compensation rules) so policy questions are answered from grounded evidence, not guesses.
- **Tool Calling** — every action that touches real data (flight status, bookings, refunds, escalations) goes through an authorized MCP tool.
- **Evaluation** — dedicated benchmark suites for planning, retrieval, and context-management strategies, so design choices are backed by measured comparisons rather than assumptions.

## Problem Statement

An airline / travel agency support desk needs an agent that can reliably:

- Determine the current status of a flight.
- Handle delays and cancellations.
- Identify the customers affected by a disruption.
- Propose rebooking alternatives.
- Apply compensation according to company policy.
- Answer policy questions (refunds, cancellations, VIP rules) accurately.
- Remember relevant customer information across a conversation.

A plain LLM is not sufficient for this on its own, because the task genuinely requires:

- **Database access** — real, current booking/flight/customer data, not the model's memory.
- **Deterministic tools** — lookups and calculations (refund amounts, flight status) must be exact, not generated.
- **Memory** — conversations get long and contain large tool outputs; important facts must survive without blowing up the context window.
- **Planning** — some steps are simple lookups, others are judgment calls with a real cost to getting them wrong, and the two need to be handled differently.
- **Grounded retrieval** — policy knowledge lives outside the database and must be retrieved and verified, not hallucinated.

## Use Case

**Flight Disruption Handling**

Input:
```
Flight MS202 is delayed due to weather.
```

The agent:
1. Checks the flight status.
2. Finds the bookings affected by the disruption.
3. Retrieves the relevant company policies (delay compensation, rebooking rules).
4. Decides on compensation.
5. Suggests a rebooking option.
6. Notifies the customer with a final, grounded answer.

## System Architecture

```
                         User
                          |
                          v
                      AI Agent
                          |
          +---------------+----------------+
          |                                |
          v                                v
    Planning Layer                  Memory / RAG Layer
          |                                |
          v                        +-------+-------+
    Planner Router                 |               |
          |                    Memory          Retrieval
    +-----+-----+               (STM/Episodic/  (Vector DB +
    |     |     |                Semantic)       Keyword)
   PS   ToT   LATS                   |               |
          |                          +-------+-------+
          v                                  |
    Execution Layer <-----------------------+
          |
          v
     MCP Client
          |
          v
     MCP Server
          |
      +---+---+
      |       |
    Tools  Database
```

**Components**
- **AI Agent** — the entry point that receives a user request and coordinates planning, memory, retrieval, and execution.
- **Planning Layer** — decomposes the request and routes hard decisions to the right planning algorithm.
- **Memory / RAG Layer** — supplies relevant customer facts and relevant policy context before the agent reasons or answers.
- **Execution Layer** — runs the generated plan against real tools and evaluates the outcome.
- **MCP Client / Server** — the transport and tool-hosting layer; the server exposes the tools and the database sits behind it.
- **Tools / Database** — the only path to live company data; the LLM never queries the database directly.

## Agent Capabilities

**Travel Operations**
- Flight status lookup
- Booking information retrieval
- Customer lookup
- Refund calculation
- Compensation determination

**Reasoning**
- Multi-step planning
- Multi-step decision-making
- Alternative evaluation and selection (rebooking options, compensation paths)

**Knowledge**
- Retrieval-augmented answers over airline policy documents (refunds, cancellations, VIP benefits, compensation)

**Memory**
- Short-term memory (conversation transcript + scratchpad)
- Episodic memory (important customer events)
- Semantic memory (persistent extracted facts, e.g. seat/meal/refund preferences)

## MCP Server & Tools

The MCP server (`server/server.py`) is the single point of contact between the agent and live company data. All tools are server-side, validated, and authorization-checked — the model never generates raw SQL or touches the database directly.

**Travel Status Tools** (`tools/travel_status_tools.py`)
- `get_flight_status`
- delay / disruption reason lookups

**Booking Tools** (`tools/booking_tools.py`)
- `get_booking`
- `get_affected_bookings`

**Customer Tools** (`tools/customer_tools.py`)
- customer profile / priority lookups

**Finance & Decision Tools** (`tools/finance_and_decision_tools.py`)
- `calculate_refund`
- `process_refund`
- compensation decisions

**Escalation Tools** (`tools/escalation_tools.py`)
- `create_escalation`

Shared infrastructure for the tool layer — schemas, authorization, validation, and prompts — lives in `shared/`.

## Database Design

The system runs on MySQL, defined in `db/schema.sql` and seeded from `db/data.sql`. An entity-relationship diagram is provided at `db/erd.png`.

```
Database
 |
 +-- Flights
 |
 +-- Customers
 |
 +-- Bookings
 |
 +-- Refunds
 |
 +-- Alternative Transport
 |
 +-- Airports
```

Reference data used by the tool layer is also available as JSON fixtures under `shared/data/` (`flights.json`, `bookings.json`, `customers.json`, `airports.json`, `alternative_transport.json`).

## Planning Layer

The planning layer decomposes a request into the right mix of deterministic tool calls, plain reasoning, and deliberate multi-path decisions.

- **Decomposition-First** (`planning/decomposition.py`) — generates the whole task DAG up front and executes it in dependency-safe batches. Every node is tagged `tool_call`, `reasoning`, or `planned`.
- **Dynamic Decomposition** (`planning/dynamic_decomposition.py`) — decides only the next step, executes it, observes the grounded result, and only then decides what comes next — so it can react live to surprises (e.g. zero available alternative flights).
- **Planner Selector** (`planning/planner_selector.py`) — routes any `planned` task to the right strategy: **Plan-and-Solve** for simple tasks, **Tree of Thoughts** when there are multiple viable alternatives, **LATS** for optimization that needs environment feedback.
- **Plan-and-Solve** (`planning/plan_and_solve.py`) — a sequential list of tool-bound steps executed in order.
- **Tree of Thoughts** (`planning/tree_of_thoughts.py`) — generates and scores several candidate solutions, then executes the best one.
- **LATS** (`planning/lats.py`) — a full expand → evaluate → select/backtrack tree search against the grounded environment.
- **Self-Refine / Reflexion** (`planning/self_refine.py`, `planning/reflexion.py`) — revise a draft answer using environment feedback, either in one pass or across multiple reflective trials.

Full detail on the DAG schema, task dispatch, and each algorithm is validated and evaluated in `planning/` and `planning_eval/`.

## Execution Pipeline

```
User Request
      |
      v
    Agent
      |
      v
   Planner
      |
      v
Execution Plan
      |
      v
  MCP Tools
      |
      v
   Database
      |
      v
   Response
```

`execution/grounded_executor.py` connects a generated plan to real execution: each node is dispatched by kind (`tool_call` → MCP Tool Registry, `planned` → Planner Selector, `reasoning` → plain LLM call), the plan's single terminal node produces the synthesized answer, and the result is scored against the grounded `TravelEnvironment` — feedback that also powers Self-Refine and Reflexion.

## Memory Architecture

- **Short-Term Memory** — the rolling conversation transcript, a scratchpad for state that must survive context pruning (current plan, sub-goal, high-stakes customer facts), and a queue of candidate `MemoryItem`s awaiting routing.
- **Promote-or-Drop Router** — a rule-based router (falling back to a Router LLM for unclear cases) that decides whether a memory item is forgotten or promoted to episodic memory. It never writes directly to semantic memory.
- **Episodic Memory** — important customer events (booking confirmations/cancellations, refund requests, preference changes) stored with their promotion reason for explainability.
- **Consolidation Layer** — periodically extracts persistent facts from episodic memory into semantic memory, versioning and closing out contradictory facts instead of overwriting them.
- **Semantic Memory** — durable, retrievable customer facts (e.g. seat preference, meal preference, refund preference) with expiration and conflict resolution.

```
User Message
     |
     v
Short-Term Memory (Scratchpad + MemoryItem)
     |
     v
Promote-or-Drop Router
     |
  +--+--+
  |     |
 DROP  Episodic Memory --> Consolidation --> Semantic Memory
```

## RAG Architecture

```
Knowledge Base
      |
   Chunking
      |
  Embedding
      |
  Vector DB
      |
  Retriever
      |
    Agent
```

- **Naive RAG** (`rag/naive_rag.py`) — the baseline: embed the query, run vector search, generate from the retrieved chunks.
- **Hybrid RAG** (`rag/hybrid_rag.py`) — combines semantic vector search with keyword/BM25 search, improving retrieval of exact identifiers (booking codes, flight numbers, policy names).
- **Agentic RAG** (`rag/agentic_rag.py`) — the agent decides whether retrieval is needed at all, and whether to retrieve again if the first pass wasn't sufficient.
- **Self-RAG-Style Verification** (`rag/self_rag.py`) — checks that retrieved context is relevant and that the generated answer is actually supported by that context before returning it, applied to both RAG and long-term memory retrieval.

The retrieval corpus (`rag/knowledge_base/`) covers refund policies, cancellation policies, VIP benefits, and compensation rules.

## Folder Structure

```
WanderPathA
├── agent/          # Agent entry point + schema
├── server/          # MCP server
├── tools/           # MCP tool implementations
├── shared/          # Schemas, auth, validation, data fixtures
├── planning/         # Decomposition, planner selector, PS/ToT/LATS, DAG
├── execution/        # Grounded execution pipeline
├── planning_eval/     # Planning benchmark + comparison
├── memory/           # Short-term, episodic, semantic memory + router
├── context_eval/      # Context-management strategy evaluation
├── rag/              # Naive / Hybrid / Agentic / Self-RAG
├── retrieval_eval/     # Retrieval benchmark
├── db/               # Schema, seed data, ERD
├── client/            # MCP client
├── artifacts/          # Logged planning runs
└── README.md
```

## Installation

**Requirements**
- Python 3.11+ (see `.python-version`)
- MySQL

**Setup**
```bash
git clone <repository-url>
cd WanderPathA
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file (see `.env.example`):
```
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=travel_agency
GROQ_API_KEY=your_api_key
```
Never commit `.env` or API keys to GitHub.

## Running the Project

**1. Set up the database**
```bash
mysql < db/schema.sql
mysql < db/data.sql
```

**2. Start the MCP server**
```bash
python server/server.py
```

**3. Run the agent**
```bash
python agent/agent.py
```

**4. Run the evaluation suite**
```bash
python run_benchmark.py
```

Run the full test suite with:
```bash
python -m pytest
```

## Example Request

```
Flight 2 has a 120-minute delay due to bad weather.
Identify affected bookings, assess passenger priority, find suitable
rebooking alternatives, and propose an appropriate plan.
```

## Example Output

For a decomposition-first run, the agent produces a DAG similar to:

```
t1 (tool_call: get_flight_status)         -> flight 2 status + delay reason
t2 (tool_call: get_affected_bookings)     -> bookings tied to flight 2
t3 (reasoning, depends on t2)             -> passenger priority assessment
t4 (tool_call: search_alternative_flights)-> candidate rebooking options
t5 (planned, depends on t3, t4)           -> rebooking decision (routed to
                                             Tree of Thoughts / LATS)
t6 (reasoning, depends on t1, t3, t5)     -> final synthesis (terminal node)
```

The terminal node (`t6`) returns the synthesized, grounded answer, for example:

```
Flight 2 is delayed by 120 minutes due to weather.

Affected booking: B001
Passenger priority: VIP
Recommended action: Rebook to flight MS303
Compensation: Voucher issued
```

*(Illustrative — actual content depends on live database state at run time; see `artifacts/planning-run-*.json` for real logged runs.)*

## Evaluation Results

| Component | What's Measured | Where |
|---|---|---|
| Planning | Success rate, LLM calls, latency across all 8 strategies | `planning_eval/`, `comparison_table.md`, `comparison_report.json` |
| Retrieval | Accuracy, token usage, latency across Naive / Hybrid / Agentic RAG | `retrieval_eval/results.csv` |
| Context Management | Task accuracy, input/output tokens, latency across the 4 pruning strategies | `context_eval/comparison_results.md` |

**Planning results** (5 runs per method, from `comparison_table.md`):

| Method | Success | Success Rate | Avg. LLM Calls | Avg. Latency |
|---|---|---|---|---|
| decomposition_first | 3/5 | 60.0% | — | 82.90s |
| dynamic | 2/5 | 40.0% | 3.6 | 87.52s |
| plan_and_solve | 4/5 | 80.0% | — | 77.87s |
| tree_of_thoughts | 3/5 | 60.0% | — | 22.32s |
| lats | 0/5 | 0.0% | — | 11.31s |
| lats_ungrounded | 0/5 | 0.0% | — | 8.70s |
| self_refine | 4/5 | 80.0% | 2.0 | 4.39s |
| reflexion | 4/5 | 80.0% | 1.0 | 20.24s |

## Comparison

- **Decomposition-first vs. Dynamic** — decomposition-first was both more successful (60% vs 40%) and slightly faster on the shared test set. Committing to a full plan up front worked better here, though the dynamic approach remains the safer choice when key facts (e.g. flight alternatives) are unknown at planning time.
- **Plan-and-Solve vs. Tree of Thoughts vs. LATS** — Plan-and-Solve had the strongest results (80%), Tree of Thoughts came in behind it (60%) but was noticeably faster, and LATS did not succeed in this run — its search overhead is only justified for genuinely branching, high-stakes tasks.
- **Self-Refine and Reflexion** — both matched Plan-and-Solve's 80% success rate; Self-Refine got there in a single pass at a fraction of the latency, while Reflexion needed the fewest average LLM calls thanks to early stopping on success.
- **RAG methods** — Naive RAG is the fastest baseline but struggles with exact identifiers (booking codes, flight numbers); Hybrid RAG improves on those cases by adding keyword/BM25 search; Agentic RAG trades extra latency for the ability to decide when retrieval is unnecessary or insufficient. See `retrieval_eval/results.csv` for the measured numbers.

## Project Evolution

WanderPathA was developed incrementally through multiple architectural stages:

### Stage 1 — MCP-Based Travel Agent
- Built an MCP server exposing deterministic travel tools.
- Connected tools with a real MySQL database.
- Added validation and authorization layers.

### Stage 2 — Memory and RAG Extension
- Added short-term, episodic, and semantic memory.
- Implemented promote-or-drop routing.
- Added retrieval over company policies using RAG.

### Stage 3 — Planning and Autonomous Decision Making
- Added decomposition-first and dynamic planning.
- Integrated Plan-and-Solve, Tree of Thoughts, and LATS.
- Introduced grounded execution over generated plans.

### Final Stage — Autonomous Agent Platform
The final system combines:
- Planning
- Memory
- Retrieval
- MCP Tool Execution
- Evaluation Frameworks

into one autonomous travel assistant architecture.


## Security & Reliability

The system was designed with controlled execution and safety boundaries:

### Database Safety
- The LLM never accesses the database directly.
- All database operations are performed through MCP tools.
- SQL generation by the model is completely avoided.

### Tool Validation
Every tool call passes through:
- Input schema validation.
- Entity existence checks.
- Business rule validation.

### Authorization Layer
Sensitive operations require permission checks:

Examples:
- Refund processing.
- Escalation creation.
- VIP-only actions.

### Grounded Responses
The agent only uses:
- Retrieved policy documents.
- MCP tool outputs.
- Verified memory entries.

to reduce hallucination.


## Agent Decision Flow

For every user request:


|
v
Intent Understanding
|
v
Memory Retrieval
|
v
Need External Knowledge?
|
+--+--+
| |
Yes No
| |
RAG Continue
|
v
Planning Required?
|
+---+
| |
No Yes
| |
Tool Planner Selection
|
v
Execution Through MCP
|
v
Observation
|
v
Memory Update
|
v
Final Response


The agent dynamically decides whether it needs:
- Memory retrieval.
- RAG retrieval.
- Planning.
- Direct tool execution.

## Technology Stack

| Category | Technology |
|---|---|
| Language | Python 3.11 |
| Agent Framework | LangChain |
| LLM | Google Gemini 2.5 Flash / Groq LLM |
| Protocol | Model Context Protocol (MCP) |
| Database | MySQL |
| Vector Search | Vector Database |
| Validation | Pydantic |
| Testing | Pytest |
| Version Control | Git + GitHub |


## Team Members

- Menna Sobhe
- Moun Reda
- Diana Emil

**Company:** WanderPath Travel Agency — Travel & Tourism

## Conclusion

WanderPathA turns a plain MCP tool-calling agent into a full autonomous travel assistant: a validated planning layer that picks the right strategy for each decision, an execution pipeline that grounds every action in real tools and data, a memory system that keeps relevant customer context alive across a conversation without polluting the context window, and a retrieval layer that answers policy questions from verified evidence instead of guesses. Dedicated benchmarks for planning, retrieval, and context management make these design choices measurable rather than assumed, and point toward favoring simpler, grounded strategies by default while reserving expensive search (LATS) and retrieval fallback (Agentic RAG) for the cases that actually need them.

**Future improvements** could include expanding the planning benchmark beyond 5 runs per method for tighter confidence intervals, adding real-time policy updates to the RAG knowledge base, and extending semantic memory with cross-session customer profiles.
