# Constrained ReAct Agent

This agent follows a constrained ReAct approach, where the language model must produce a structured action at every step instead of reasoning freely.

Unlike the unconstrained agent, the model is limited to a predefined set of actions, executes only one action per step, and continues until it reaches a terminal action (`final_answer`, `end_conversation`, or `escalate`) or the maximum number of reasoning steps is reached. :contentReference[oaicite:2]{index=2}

## Execution Flow

```text
              User Request
                    │
                    ▼
         Structured Language Model
                    │
                    ▼
      Select Exactly One Allowed Action
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
  Terminal Action          Tool Action
        │                       │
        │                 Execute Tool
        │                       │
        │                       ▼
        │               Tool Observation
        │                       │
        └───────────────┬───────┘
                        ▼
               Next Reasoning Step
                        │
                        ▼
                 Final Response
```

## Features

- Structured outputs using a Pydantic schema.
- Only predefined actions are allowed.
- Executes one action per reasoning step.
- Uses tool observations instead of guessing.
- Limits the reasoning process to a fixed number of steps.
- Escalates to a human agent if the request cannot be resolved safely.

## Available Actions

- get_booking_history
- get_flight_status
- get_delay_duration
- check_alternative_transport
- check_refund_eligibility
- calculate_refund_amount
- process_refund
- issue_travel_voucher
- escalate
- end_conversation
- final_answer

## How to Run

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file and add your API keys:

```env
GOOGLE_API_KEY=your_google_api_key
```

You can obtain your API keys from:

- Google AI Studio: https://aistudio.google.com/api-keys
- Tavily: https://tavily.com

3. Run the agent:

```bash
python -m constrained_react.agent
```