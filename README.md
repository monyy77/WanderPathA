# WanderPath Travel Agency – Memory & RAG Lab

## Team Members

- Menna Sobhe
- Moun Reda
- Diana Emil

## Company

**WanderPath Travel Agency**

**Industry:** Travel & Tourism

---

## Project Overview

This project extends the existing **WanderPath Travel Agency MCP Server** by adding a complete memory and retrieval architecture.

The original agent could access live company data through MCP tools, but it had two major limitations:

- Conversation information was not preserved effectively across interactions.
- The agent could not reliably reason over company knowledge outside direct MCP tool calls.

This project adds:

- Short-Term Memory
- Scratchpad
- Context Window Management
- Promote-or-Drop Routing
- Episodic Memory
- Semantic Memory
- Memory Consolidation
- Vector Database
- Naive RAG
- Hybrid Search
- Agentic RAG
- Self-RAG-style Verification
- End-to-End Agent Integration

The implementation extends the existing `mcp_server/` and `db/` instead of rebuilding them.

---

## Problem Statement

Travel support conversations can become long and contain large tool outputs such as:

- Booking information
- Flight information
- Customer profiles
- Refund information
- Cancellation details
- Rebooking options
- Company policies

Keeping the entire conversation inside the context window increases token usage and can cause important customer information to be lost.

At the same time, many questions cannot be answered directly from the database. Important knowledge such as refund policies, cancellation rules, VIP benefits, compensation rules, and travel policies must be retrieved from external knowledge.

The goal is therefore to provide the agent with both:

1. **Long-term memory** of important customer information
2. **Grounded retrieval** of company knowledge

---

## Overall Architecture

```text
                         User
                          |
                          v
                    Travel Agent
                          |
             +------------+------------+
             |                         |
             v                         v
      Short-Term Memory            Retrieval Layer
             |                         |
       +-----+-----+             +-----+-----+
       |           |             |           |
   Transcript   Scratchpad    Vector DB    Keyword Search
       |                         |           |
       v                         v           v
Context Management          Naive / Hybrid / Agentic RAG
       |
       v
Promote-or-Drop Router
       |
    +--+--+
    |     |
  DROP  PROMOTE
    |     |
 Forget   v
       Episodic Memory
             |
       Periodic Consolidation
             |
             v
       Semantic Memory
             |
             v
       Memory Retrieval
             |
             +-------------+
                           |
                           v
                  Self-RAG Verification
                           |
                           v
                       Final Answer
```

---

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
│
├── agent/
│   ├── agent.py
│   ├── schema.py
│   └── ...
│
├── memory/
│   ├── short_term_memory.py
│   ├── scratchpad.py
│   ├── memory_models.py
│   ├── memory_item_factory.py
│   ├── metadata_builder.py
│   ├── router.py
│   ├── episodic_memory.py
│   ├── semantic_memory.py
│   ├── consolidation.py
│   ├── fact_extractor_llm.py
│   └── ...
│
├── context_eval/
│   ├── context_strategies.py
│   ├── long_context_tests.py
│   └── ...
│
├── rag/
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── naive_rag.py
│   ├── hybrid_rag.py
│   ├── agentic_rag.py
│   ├── self_rag.py
│   └── ...
│
├── retrieval_eval/
│   ├── test_questions.py
│   ├── evaluation.py
│   └── ...
│
├── mcp_server/
│   └── ...
│
└── db/
    ├── schema.sql
    ├── data.sql
    └── erd.png
```

---

## Short-Term Memory

Short-Term Memory contains three independent structures:

**Message Buffer** — Stores the rolling conversation transcript.

**Scratchpad** — Stores information that must survive context pruning:

- Current plan
- Current sub-goal
- Working state
- High-stakes customer facts

**MemoryItem Queue** — Stores customer information waiting for the Promote-or-Drop Router.

```text
Short-Term Memory
├── messages
├── scratchpad
└── items
```

The scratchpad is injected into the agent prompt after context pruning, preventing important state from being removed.

---

## Context Window Management

Four context management strategies are implemented:

- Sliding Window
- Observation / Tool Output Masking
- Recursive Summarization
- Zone-Based Pruning

All strategies are evaluated using long-context conversations containing:

- Multiple customer turns
- Large MCP tool outputs
- Important information buried early in the conversation
- Repeated irrelevant observations

Each strategy is evaluated using:

- Task accuracy
- Input tokens
- Output tokens
- Latency

The selected strategy is integrated into the live agent loop.

---

## Promote-or-Drop Router

The router decides what should survive short-term memory.

```text
MemoryItem
    |
    v
Rule-Based Router
    |
    +---- PROMOTE ----> Episodic Memory
    |
    +---- DROP --------> Forget
    |
    +---- Unknown
             |
             v
         Router LLM
             |
        +----+----+
        |         |
     PROMOTE     DROP
```

The router never writes directly to Semantic Memory.

### Router LLM

The Router LLM is responsible only for deciding whether a memory item should be retained.

It returns:

- `PROMOTE + reason`
- or `DROP + reason`

The Router LLM is separate from the Fact Extractor LLM.

> **Router LLM** — "What should I remember?"
>
> **Fact Extractor LLM** — "What exactly is the persistent fact?"

---

## Episodic Memory

Important customer events are stored as `Episode` objects.

Examples include:

- Booking confirmations
- Booking cancellations
- Refund requests
- Customer preferences
- Profile updates
- Important travel events

An episode contains:

- `content`
- `entity_type`
- `entity_id`
- `source`
- `reason`
- `timestamp`
- `metadata`

The routing reason is preserved so that every promotion decision is explainable.

---

## Semantic Memory

Semantic Memory stores persistent facts extracted from episodic memories.

Examples:

- `seat_preference` → window
- `meal_preference` → vegetarian
- `refund_preference` → voucher

Semantic facts support:

- Versioning
- Expiration
- Validity periods
- Conflict resolution
- Entity-based retrieval

### Consolidation Layer

Semantic Memory is never written directly by the Router. Instead:

```text
Episodic Memory
      |
      v
Periodic Consolidation
      |
      v
Rule-Based Extraction
      |
      +---- Fact found ----> Semantic Fact
      |
      +---- No fact
              |
              v
        Fact Extractor LLM
              |
              v
        Semantic Fact
```

The consolidation layer handles:

- New facts
- Updated facts
- Contradictory facts
- Fact versioning
- Expiration
- Historical validity

When a fact changes, the previous version is closed instead of silently overwritten.

---

## Memory Retrieval

Relevant semantic memories are retrieved for the current customer query.

```text
User Query
    |
    v
Semantic Memory Retrieval
    |
    v
Relevant Customer Facts
    |
    v
Agent Context
```

This allows the agent to remember information from previous interactions.

---

## High-Stakes Scratchpad Facts

The scratchpad detects important information from customer messages.

Examples:

- Accessibility requirements
- Budget limits
- Passport constraints
- Refund preferences
- Booking conditions

Detection uses:

```text
Rules
  |
  +---- Found ----> Pin Fact
  |
  +---- Not Found
          |
          v
        LLM
          |
          v
       Pin Fact
```

Each extracted fact is also represented as a `MemoryItem` so it can participate in the long-term memory pipeline.

---

## Vector Database

The retrieval system uses a real vector database architecture consisting of:

- Vector Index
- Metadata Store
- Metadata Index

The vector index supports approximate nearest-neighbor retrieval.

Each document chunk contains:

- Embedding
- Original Text
- Metadata

Metadata can include:

- source
- document type
- section
- date
- entity

Metadata filtering is applied before or during similarity search.

### Document Processing Pipeline

```text
Company Documents
      |
      v
Document Chunking
      |
      v
Embeddings
      |
      v
Vector Database
      |
      +---- Vector Index
      +---- Metadata Store
      +---- Metadata Index
```

The retrieval corpus contains company knowledge such as:

- Refund policies
- Cancellation policies
- VIP benefits
- Travel voucher rules
- Compensation policies
- Airport information
- Customer support policies

---

## RAG Architectures

Three retrieval architectures are implemented.

### Naive RAG

```text
Query
  |
Embedding
  |
Vector Search
  |
Retrieved Chunks
  |
LLM
  |
Answer
```

Naive RAG provides the baseline retrieval architecture.

### Hybrid Search

Hybrid Search combines:

```text
Semantic Vector Search
        +
Keyword / BM25 Search
        |
        v
Merged Ranking
        |
        v
Retrieved Context
```

This improves retrieval for exact identifiers such as:

- Booking codes
- Flight numbers
- Policy names
- Error codes
- Exact business terms

### Agentic RAG

Agentic RAG allows the agent to decide:

- What should be retrieved
- Whether retrieval is necessary
- Whether another retrieval is required
- Whether the retrieved information is sufficient

```text
Question
   |
   v
Agent Reasoning
   |
   v
Retrieve
   |
   v
Observe Results
   |
   +---- Sufficient ----> Generate
   |
   +---- Insufficient --> Retrieve Again
```

---

## Retrieval Evaluation

All retrieval architectures are evaluated using the same domain-specific question set.

The evaluation measures:

- Accuracy
- Token usage per query
- Latency per query

The test set contains:

- General policy questions
- Exact identifier questions
- Multi-part questions
- Questions requiring multiple retrieval steps

The final retrieval architecture is selected based on measured performance and the actual query patterns of WanderPath Travel Agency.

---

## Self-RAG-Style Verification

The system performs explicit verification before returning an answer.

### Retrieval Relevance

```text
Retrieved Context
       |
       v
Is the context relevant?
       |
   +---+---+
   |       |
  Yes      No
   |       |
   v       v
Generate  Reject / Retry
```

### Answer Support

```text
Generated Answer
       |
       v
Is the answer supported by retrieved evidence?
       |
   +---+---+
   |       |
  Yes      No
   |       |
   v       v
Return   Reject / Regenerate
```

Self-RAG-style verification is applied to both:

- RAG retrieval
- Long-term memory retrieval

This prevents unsupported information from being presented as a trusted answer.

---

## Agent Integration

The memory and retrieval systems are part of the live agent loop.

```text
User Message
     |
     v
Short-Term Memory
     |
     +---- Scratchpad
     |
     +---- MemoryItem
              |
              v
        Promote-or-Drop
              |
        +-----+-----+
        |           |
       DROP       EPISODIC
                    |
                    v
              Consolidation
                    |
                    v
              Semantic Memory
     
     +----------------------+
     |
     v
Context Management
     |
     v
Memory + RAG Retrieval
     |
     v
Self-RAG Verification
     |
     v
Agent Reasoning
     |
     v
MCP Tools
     |
     v
Final Answer
```

The existing MCP Server and MySQL database remain the source of live company data.

---

## End-to-End Workflow

```text
Conversation
    |
    v
Short-Term Memory
    |
    v
Context Management
    |
    v
Promote-or-Drop Router
    |
    +---- DROP
    |
    +---- PROMOTE
             |
             v
        Episodic Memory
             |
             v
       Consolidation Layer
             |
             v
       Semantic Memory
             |
             v
      Memory Retrieval
             |
             +----------------+
                              |
                              v
                         RAG Retrieval
                              |
                              v
                    Self-RAG Verification
                              |
                              v
                         AI Agent
                              |
                              v
                         MCP Tools
                              |
                              v
                         User Answer
```

---

## Testing

The project includes tests for:

- Short-term memory
- Scratchpad persistence
- High-stakes fact extraction
- MemoryItem creation
- Promote-or-Drop routing
- Episodic memory
- Semantic memory
- Consolidation
- Fact versioning
- Conflict resolution
- Context window strategies
- Vector retrieval
- Naive RAG
- Hybrid Search
- Agentic RAG
- Self-RAG verification
- End-to-end agent integration

Run the tests with:

```bash
python -m pytest
```

---

## Running the Project

### 1. Clone the Repository

```bash
git clone <repository-url>
cd WanderPathA
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file:

```env
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=travel_agency
GROQ_API_KEY=your_api_key
```

> Never commit `.env` or API keys to GitHub.

### 4. Database Setup

Initialize the existing WanderPath database:

```bash
mysql < db/schema.sql
mysql < db/data.sql
```

The project reuses the existing database and MCP infrastructure.

### 5. Run the MCP Server

```bash
python server/server.py
```

### 6. Run the Agent

```bash
python agent/agent.py
```

---

## Technologies

- Python
- MySQL
- Model Context Protocol (MCP)
- LangChain
- Groq
- Llama 3.3 70B
- Pydantic
- Vector Database
- BM25
- RAG
- Agentic RAG
- Self-RAG-style Verification
- Embeddings
- Approximate Nearest Neighbor Search

---

## Security and Safety

The project follows the original MCP security architecture:

- No direct database access from the LLM
- Server-side validation
- Authorization checks
- Controlled MCP tools
- No raw SQL generated by the model
- Environment variables for secrets
- No committed API keys
- Grounded RAG responses
- Verification of retrieved evidence
- Explicit memory routing
- Versioned semantic facts

---

## Key Design Principles

- Short-term memory and scratchpad are separate.
- Context pruning must never destroy the scratchpad.
- The Router only decides between forgetting and episodic promotion.
- The Router never writes directly to Semantic Memory.
- Semantic Memory is created through periodic consolidation.
- Contradictory facts are versioned instead of silently overwritten.
- RAG answers must be grounded in retrieved information.
- Retrieval quality is evaluated using real test questions.
- Multiple retrieval architectures are compared before selecting the final approach.
- The existing MCP Server and database are reused rather than duplicated.

---

## Project Result

The final system transforms WanderPath from an MCP-only travel support agent into a memory-aware and knowledge-grounded agent.

It can now:

- Maintain short-term conversational state
- Preserve important customer information
- Forget irrelevant information
- Promote valuable memories to episodic memory
- Consolidate episodes into semantic facts
- Handle changing and conflicting customer facts
- Retrieve relevant long-term memories
- Search company knowledge using vector and keyword retrieval
- Perform Naive, Hybrid, and Agentic RAG
- Verify retrieved evidence before answering
- Continue using the existing MCP tools and database

```text
WanderPath MCP Agent
        +
Short-Term Memory
        +
Long-Term Memory
        +
Vector Retrieval
        +
RAG
        +
Self-RAG Verification
        =
Grounded Memory-Aware Travel Agent
```
