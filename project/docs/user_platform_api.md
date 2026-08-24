# WanderPath User Platform API

Base URL: `/api`

All endpoints expect and return `application/json`.

## Agents

| id            | name           | purpose                                                  |
|---------------|----------------|----------------------------------------------------------|
| `memory`      | Memory Agent   | Remembers user preferences, past trips, and profile data |
| `planning`    | Planning Agent | Builds full trip itineraries day-by-day                  |
| `flight`      | Flight Agent   | Searches, compares, and books flights                    |
| `refund`      | Refund Agent   | Handles cancellation and refund requests                 |
| `vip`         | VIP Agent      | Concierge perks, upgrades, and exclusive experiences     |

## POST /api/chat

Send a user message to the currently selected agent and receive a streamed
or single assistant response.

### Request

```json
{
  "agent_id": "planning",
  "session_id": "sess_abc123",
  "message": "Plan a 5-day trip to Kyoto in November"
}
```

| field        | type   | required | description                                |
|--------------|--------|----------|--------------------------------------------|
| `agent_id`   | string | yes      | One of the agent ids above.                |
| `session_id` | string | yes      | Stable conversation session id.            |
| `message`    | string | yes      | The user's message text.                   |

### Response — 200

```json
{
  "session_id": "sess_abc123",
  "agent_id": "planning",
  "message_id": "msg_01HZ...",
  "role": "assistant",
  "content": "Here is a day-by-day plan for Kyoto...",
  "status": "completed",
  "steps": [
    { "label": "Understanding request", "state": "done" },
    { "label": "Selecting destinations", "state": "done" },
    { "label": "Drafting itinerary", "state": "done" }
  ],
  "created_at": "2026-08-23T20:31:00Z"
}
```

| field        | type                     | description                                      |
|--------------|--------------------------|--------------------------------------------------|
| `session_id` | string                   | Echoed session id.                               |
| `agent_id`   | string                   | Echoed agent id.                                 |
| `message_id` | string                   | Server-assigned message id.                      |
| `role`       | `"assistant"`            | Always `assistant` for responses.                |
| `content`    | string                   | The assistant reply text (markdown allowed).     |
| `status`     | `completed` \| `error`   | Terminal status of the turn.                     |
| `steps`      | `Step[]`                 | Ordered execution steps the agent performed.     |
| `created_at` | string (ISO 8601)        | Timestamp of the response.                       |

### Step

```ts
type Step = {
  label: string;
  state: "pending" | "running" | "done" | "error";
};
```

### Errors

| status | meaning                |
|--------|------------------------|
| 400    | Bad request body.      |
| 404    | Unknown `agent_id`.    |
| 500    | Internal agent error.  |

```json
{ "error": "agent_not_found", "message": "Unknown agent id" }
```

## GET /api/agents

Returns the catalog of available agents.

```json
{
  "agents": [
    {
      "id": "memory",
      "name": "Memory Agent",
      "tagline": "Remembers every detail of your journey",
      "description": "Stores preferences, past trips, and profile context.",
      "icon": "brain",
      "accent": "indigo"
    }
  ]
}
```
