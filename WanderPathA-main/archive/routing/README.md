# Routing Agent

## Overview

The Routing Agent is a deterministic travel support assistant that uses a single Large Language Model (LLM) call to classify a customer's request into one predefined category. Once the request is classified, the remaining workflow is executed using deterministic Python code and specialized tools.

Unlike a fully autonomous agent, the Routing Agent does not decide which tools to use dynamically. Instead, it only determines the customer's intent, making the system faster, more predictable, and easier to test.

---

# Architecture

```
Customer Request
        │
        ▼
 Google Gemini
 (Single Classification)
        │
        ▼
Route Decision
        │
        ├── Refund
        ├── Rebooking
        ├── Flight Information
        └── Escalation
                │
                ▼
      Deterministic Python Logic
                │
                ▼
          Tool Execution
                │
                ▼
          Final Response
```

---

# Supported Categories

The model classifies every customer request into one of the following categories:

* Refund
* Rebooking
* Flight Information
* Escalation

Only one category can be selected for each request.

---

# Project Structure

```
routing/
├── README.md
└── main.py
```

---

# Tools Used

Depending on the selected route, the agent uses different tools.

## Refund

* CheckRefundEligibility
* CalculateRefundAmount
* ProcessRefund

---

## Flight Information

* get_flight_status
* get_delay_duration
* check_connection_risk

---

## Rebooking

* get_flight_status
* get_delay_duration
* check_alternative_transport

---

## Escalation

* escalate_to_human

---

# Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root.

```env
GOOGLE_API_KEY=YOUR_API_KEY
```

The project uses `python-dotenv` to load the API key automatically.

---

# Running the Agent

From the project root:

```bash
python main.py
```

Choose:

```
3
```

to start the Routing Agent.

---

# Example

### User

```
What is the status of my flight?
```

### Output

```
Flight Information
-------------------------
Flight ID: MS101
Status: On Time
Delay: 0 minutes
Connection Risk: False
```

---

### User

```
I want a refund for my cancelled flight.
```

### Output

```
Agent: Refund processed successfully.
Refund Amount: $1200
```

---

# Advantages

* Only one LLM call per request.
* Fast response time.
* Lower token usage.
* Predictable execution.
* Easy to test and debug.
* Business logic remains in Python.

---

# Limitations

The Routing Agent has several limitations because it relies on a single classification step.

* It can only select one category for each request.
* Multi-intent requests may be routed incorrectly.
* Incorrect classification leads to the wrong workflow.
* It cannot ask follow-up questions before making a decision.
* Classification quality depends on the system prompt and the LLM.

---

# Example Failure Cases

## Multiple Intents

**User**

```
My flight was cancelled. I want a refund and another flight.
```

Possible result:

```
Escalation
```

The agent cannot process multiple workflows simultaneously because it must select only one route.

---

## Incorrect Classification

**User**

```
I want a refund for my cancelled flight.
```

Expected route:

```
Refund
```

Possible result:

```
Flight Information
```

A single incorrect classification causes the wrong workflow to execute.

---

## Ambiguous Request

**User**

```
My flight was cancelled. What should I do?
```

Possible result:

```
Escalation
```

Since the user's intent is unclear, the agent may choose a different route than expected.

---

# Technologies

* Python
* LangChain
* Google Gemini
* Pydantic
* python-dotenv

---

# Future Improvements

* Support multiple intents in a single request.
* Ask follow-up questions when the user's intent is ambiguous.
* Improve prompt engineering to reduce classification errors.
* Add confidence scores before executing a workflow.
* Integrate with real airline APIs and booking systems.
