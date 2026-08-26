# Demo Scenarios

## Scenario 1: Flight Delay

### Input
```
Flight MS101 is delayed by 120 minutes.
Replan all affected bookings.
```

### Expected Flow
```
User Request
    ↓
Agent
    ↓
Planner
    ↓
MCP Tools
    ↓
Query Flight and Booking Data from Database
    ↓
Retrieve Relevant Context using Memory/RAG
    ↓
Final Response
```

### Expected Output
- Affected bookings are identified.
- Alternative plans are generated.
- Updated itinerary information is provided.

---

## Scenario 2: Flight Cancellation

### Input
```
Flight MS202 has been cancelled.
Find alternative options for affected passengers.
```

### Expected Flow
```
User Request
    ↓
Agent
    ↓
Planner
    ↓
MCP Tools
    ↓
Retrieve Cancelled Flight and Passenger Data from Database
    ↓
Find Alternative Flight Options
    ↓
Retrieve Previous Context using Memory/RAG
    ↓
Final Response
```

### Expected Output
- Affected passengers are identified.
- Alternative flights are suggested.
- Refund or compensation options are provided when applicable.

---

## Scenario 3: Booking Modification

### Input
```
Change my booking date for booking B001.
```

### Expected Flow
```
User Request
    ↓
Agent
    ↓
Planner
    ↓
MCP Tools
    ↓
Validate Booking and Available Flights from Database
    ↓
Update Booking Information
    ↓
Retrieve Customer Context using Memory/RAG
    ↓
Final Response
```

### Expected Output
- Booking information is updated successfully.
- New itinerary details are provided.

---

## Scenario 4: Refund Request

### Input
```
I want a refund for my cancelled flight.
```

### Expected Flow
```
User Request
    ↓
Agent
    ↓
Planner
    ↓
MCP Tools
    ↓
Check Refund Eligibility and Calculate Refund using Database Data
    ↓
Store Refund Result
    ↓
Retrieve Relevant Memory/RAG Context
    ↓
Final Response
```

### Expected Output
- Refund eligibility is determined.
- Refund amount is calculated.
- Refund status is provided to the customer.

---

## Scenario 5: Customer Support Escalation

### Input
```
Escalate my issue to a manager.
```

### Expected Flow
```
User Request
    ↓
Agent
    ↓
Planner
    ↓
MCP Tools
    ↓
Create Escalation Record in Database
    ↓
Retrieve Previous Customer Context using Memory/RAG
    ↓
Final Response
```

### Expected Output
- Customer issue is escalated successfully.
- Escalation status and related information are provided.
