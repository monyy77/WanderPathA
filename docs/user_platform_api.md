# WanderPathA User Platform API Specification

## 1. Purpose

This document defines the API used by the WanderPathA User Platform.
The platform provides a unified conversational interface that allows customers to interact with different AI agents through a single application.

The User Platform does not communicate directly with MCP Server or tools. All requests are routed through the Agent Router layer.

---

## 2. Available AI Agents

The system exposes five specialized agents.

### Memory Agent

**Agent ID:** `memory`

**Responsibilities:**
- Maintain conversation context.
- Retrieve previous customer information.
- Store important user interactions.
- Provide context for other agents.

---

### Planning Agent

**Agent ID:** `planning`

**Implementation:** `planning/planning_agent.py`

**Responsibilities:**
- Analyze complex travel requests.
- Perform decomposition.
- Generate DAG execution plans.
- Select available MCP tools.
- Coordinate multi-step workflows.

---

### Flight Agent

**Agent ID:** `flight`

**Implementation:** `state_graph/graphs/flight_rebooking.py`

**Responsibilities:**
- Flight status inquiries.
- Flight rebooking.
- Booking modification workflows.

---

### Refund Agent

**Agent ID:** `refund`

**Implementation:** `state_graph/refundGraph/refund_graph.py`

**Responsibilities:**
- Refund eligibility.
- Refund calculation.
- Refund processing.
- Human approval workflow when required.

---

### VIP Agent

**Agent ID:** `vip`

**Implementation:** `state_graph/graphs/vip_trip_customization.py`

**Responsibilities:**
- VIP customer validation.
- Premium trip customization.
- Hotel upgrade.
- Transport reservation.
- Activity booking.

---

## 3. Chat API

### Endpoint

```
POST /api/chat
```

Used by the User Platform to communicate with AI agents.

### Request

**Headers:**

```
Content-Type: application/json
```

**Body:**

```json
{
  "agent": "planning",
  "message": "I need to change my trip",
  "session_id": "session_001",
  "customer_id": "C001"
}
```

### Request Parameters

| Parameter | Type | Description |
|---|---|---|
| agent | string | Target AI agent |
| message | string | User message |
| session_id | string | Conversation session |
| customer_id | string | Customer identifier |

**Allowed agents:**
- memory
- planning
- flight
- refund
- vip

---

## 4. Agent Routing

The backend routes requests according to selected agent.

**Example:**

```
agent = planning
        |
        v
planning_agent.py
        |
        v
MCP Tool Registry
        |
        v
Execution
```

**Example:**

```
agent = refund
        |
        v
refund_graph.py
        |
        v
Finance Tools
```

---

## 5. Successful Response

**HTTP:** `200 OK`

**Response:**

```json
{
  "agent": "planning",
  "session_id": "session_001",
  "response": "I created a travel modification plan.",
  "execution": {
      "status": "completed"
  }
}
```

**Fields:**

| Field | Description |
|---|---|
| agent | Agent used |
| session_id | Current conversation |
| response | Assistant answer |
| execution | Workflow information |

---

## 6. Execution Metadata

For workflows that use planning or state graphs:

**Example:**

```json
{
 "execution": {
    "status": "completed",
    "steps": [
       "analyze_request",
       "create_plan",
       "execute_tools"
    ]
 }
}
```

---

## 7. Conversation History

The User Platform stores:
- session_id
- agent
- messages
- timestamps

Conversation history is managed through the backend memory layer.

---

## 8. Agent Switching

Users can switch between agents from the same interface.

**Example:**

```
Customer
 |
Planning Agent
 |
switch
 |
Refund Agent
```

The frontend sends the new selected agent in the next request.

**Example:**

```json
{
 "agent": "refund",
 "message": "Can I get my money back?"
}
```

---

## 9. Security Constraints

The User Platform:
- Cannot access database directly.
- Cannot call MCP tools directly.
- Cannot execute tool names.
- Cannot bypass agent routing.

Only backend agents can interact with:
- MCP Server
- Tool Registry
- Database
- State Graph Workflows

---

## 10. Final User Platform Components

The frontend contains:

```
User Platform
├── Agent Selector
├── Chat Interface
├── Message History
├── Session Management
└── Agent Status Display
```

**Supported agents:**
- Memory
- Planning
- Flight
- Refund
- VIP
