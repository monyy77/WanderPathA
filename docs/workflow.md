# Workflow

## Overview

The WanderPath Travel Agency agent follows a structured workflow that transforms a user's travel disruption request into a grounded and evaluated response.

The workflow combines:
- Planning and task decomposition
- Multi-strategy reasoning
- MCP tool execution
- Database-grounded decisions
- Evaluation and refinement

The complete workflow is:

```
User Goal
    |
    v
Planning Agent
    |
    v
Task Decomposition
    |
    v
DAG Construction & Validation
    |
    v
Planner Selector
    |
    +--------------------+--------------------+
    |                    |                    |
    v                    v                    v
Plan-and-Solve     Tree of Thoughts        LATS
    |                    |                    |
    +--------------------+--------------------+
                         |
                         v
              Grounded Execution Pipeline
                         |
                         v
                 MCP Tool Registry
                         |
                         v
                    MCP Server
                         |
                         v
                     Database
                         |
                         v
                  Environment Feedback
                         |
                         v
                    Evaluation
                         |
                         v
              Self-Refine / Reflexion
                         |
                         v
                  Final Response
```

---

## 1. User Goal

The workflow starts when a customer or travel employee provides a goal or request.

Example:

```
Flight 2 has a 120-minute delay because of bad weather.
Identify affected bookings, find alternative flights,
and propose compensation options.
```

The request represents a high-level objective that may require multiple steps, database queries, reasoning, and decision-making.

---

## 2. Planning Agent

The Planning Agent is responsible for converting the user goal into an executable strategy.

Its responsibilities:
- Understand the user's intent.
- Identify required actions.
- Decide which steps require:
  - Direct tool calls.
  - Reasoning.
  - Advanced planning algorithms.
- Create an execution strategy.

Unlike a simple LLM agent that directly calls tools, the Planning Agent first reasons about how to solve the problem.

---

## 3. Task Decomposition

The Planning Agent decomposes the main goal into smaller independent tasks.

Example:

Original goal:
```
Handle flight disruption
```

becomes:

```
Task 1: Get flight status
Task 2: Find affected bookings
Task 3: Check passenger priority
Task 4: Find alternative flights
Task 5: Choose the best rebooking option
Task 6: Generate final recommendation
```

Each task is classified according to its nature:

**TOOL_CALL**

Tasks that require deterministic information retrieval.

Example:
```
get_flight_status()
get_affected_bookings()
```

**REASONING**

Tasks that require analyzing existing information.

Example:
```
Assess passenger priority based on VIP status and travel conditions
```

**PLANNED**

Tasks requiring deeper decision-making or exploring multiple possibilities.

Example:
```
Choose the optimal rebooking strategy
```

These tasks are passed to the Planner Selector.

---

## 4. DAG Construction and Validation

After decomposition, tasks are represented as a Directed Acyclic Graph (DAG).

The DAG defines:
- Task dependencies.
- Execution order.
- Available parallel tasks.

Example:

```
Get Flight Status
        |
        v
Find Affected Bookings
        |
        v
Assess Passenger Priority
        |
        +----------------+
        |                |
        v                v
Find Alternatives   Calculate Compensation
        |
        v
Choose Rebooking Plan
        |
        v
Final Recommendation
```

Before execution, the DAG is validated to ensure:
- No circular dependencies exist.
- All required tasks are defined.
- The execution order is correct.

---

## 5. Planner Selector

The Planner Selector chooses the appropriate reasoning strategy for complex planning tasks.

It analyzes the task requirements and routes it to one of three planning methods.

### 5.1 Plan-and-Solve

Used for tasks that can be solved through sequential planning.

Process:
```
Generate Plan
      |
      v
Execute Steps Sequentially
      |
      v
Return Result
```

Example:
```
Find available flight
→ Check passenger information
→ Select suitable option
```

Advantages:
- Simple.
- Fast.
- Suitable for structured tasks.

### 5.2 Tree of Thoughts (ToT)

Used when multiple possible solutions exist.

The agent generates several candidate solutions, evaluates them, and selects the best one.

Workflow:
```
Generate Candidates
        |
        +---- Option A
        |
        +---- Option B
        |
        +---- Option C
        |
        v
Evaluate Candidates
        |
        v
Select Best Solution
```

Example:

Possible rebooking options:
```
Option 1: Same day alternative flight
Option 2: Next day flight + hotel compensation
Option 3: Refund request
```

The agent compares them based on:
- Cost.
- Passenger preference.
- Availability.
- Company policy.

### 5.3 LATS (Language Agent Tree Search)

Used for complex optimization problems requiring exploration and feedback.

The agent:
- Generates possible actions.
- Executes or evaluates them.
- Scores outcomes.
- Explores better alternatives.

Workflow:
```
Generate Actions
       |
       v
Evaluate Environment
       |
       v
Select Best Branch
       |
       v
Backtrack if Needed
```

LATS is useful when choosing the optimal solution requires searching through multiple possible paths.

---

## 6. Grounded Execution Pipeline

After planning, tasks are executed through the grounded execution layer.

The pipeline connects:
```
Planner
   |
   v
Execution Engine
   |
   v
MCP Tool Registry
   |
   v
MCP Server
   |
   v
Database
```

The execution layer ensures that:
- Tools are real registered MCP tools.
- Arguments are validated.
- Results come from the actual database.
- Decisions are based on real travel data.

Example:

Instead of generating:
```
Flight XY123 is available
```
from model knowledge, the agent executes:
```
search_alternative_flights()
```
and receives the actual available flights.

---

## 7. MCP Tool Execution

The MCP Server provides access to travel agency capabilities.

Examples of executed tools:

**Travel Status Tools**
```
get_flight_status()
get_affected_bookings()
```

**Customer Tools**
```
get_customer_information()
check_customer_priority()
```

**Finance Tools**
```
calculate_refund_amount()
calculate_compensation()
issue_travel_voucher()
```

Each tool interacts with the database to retrieve or modify information.

---

## 8. Database Grounding

The database represents the real travel environment.

It contains:
- Flights.
- Customers.
- Bookings.
- Refunds.
- Alternative transportation.
- Employees.

The database prevents the agent from making unsupported assumptions.

All recommendations are based on actual available data.

---

## 9. Evaluation

After execution, the generated response is evaluated.

The evaluation checks:
- Whether the requested goal was achieved.
- Whether the recommendation follows company rules.
- Whether the selected solution is feasible.
- Whether database information was correctly used.

The evaluation produces feedback about the quality of the result.

---

## 10. Self-Refine and Reflexion

If the generated answer does not satisfy evaluation criteria, improvement loops are applied.

**Self-Refine**

The agent:
- Reviews its answer.
- Identifies weaknesses.
- Generates an improved response.

Workflow:
```
Initial Answer
      |
      v
Critique
      |
      v
Improved Answer
```

**Reflexion**

The agent uses previous failures as reflection memory.

Workflow:
```
Attempt
   |
   v
Failure Analysis
   |
   v
Reflection Memory
   |
   v
New Attempt
```

This allows the agent to improve future decisions.

---

## 11. Final Response

After successful execution and evaluation, the system returns the final recommendation.

Example:

```
Flight MS202 is delayed by 120 minutes.

Affected passengers:
- Ahmed Ali
- Sara Mohamed (VIP)

Recommended actions:
- Rebook Sara on alternative flight MS303.
- Provide compensation voucher according to policy.
- Notify affected customers.
```

The final response is:
- Generated from executed tasks.
- Grounded in database results.
- Verified through evaluation.

---

## Summary

The complete workflow transforms a simple customer request into an intelligent decision process:

```
User Goal
    ↓
Planning Agent
    ↓
Task Decomposition
    ↓
DAG Planning
    ↓
Planner Selection
    ↓
Reasoning Strategy
(Plan-and-Solve / ToT / LATS)
    ↓
Grounded Execution
    ↓
MCP Tools + Database
    ↓
Evaluation
    ↓
Refinement
    ↓
Final Response
```

This workflow enables WanderPath Travel Agency to handle complex flight disruptions using reliable, explainable, and data-grounded agent reasoning.
