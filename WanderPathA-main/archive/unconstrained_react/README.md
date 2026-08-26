# Unconstrained React Agent

This agent follows an unconstrained approach, allowing the language model to freely decide how to solve a user's request. Based on the conversation, it determines whether to respond directly or invoke one or more available tools.

## Execution Flow

```text
User Request
      │
      ▼
Language Model
      │
      ├── Answer directly
      │
      └── Call one or more tools
               │
               ▼
         Tool Results
               │
               ▼
        Final Response
```

## How to Run

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file and add your API keys:

```env
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
```

You can obtain your API keys from:
- Google AI Studio: https://aistudio.google.com/api-keys
- Tavily: https://tavily.com

3. Run the agent:

```bash
python -m unconstrained_react.agent
```