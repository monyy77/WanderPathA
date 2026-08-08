WanderPath Travel Agency – Memory & RAG Lab

Team Members

Menna Sobhe

Moun Reda

Diana Emil

Company

WanderPath Travel Agency

Industry

Travel & Tourism

Project Overview

This project extends the existing WanderPath Travel Agency MCP Server by adding a complete Memory and RAG architecture.

The system enables the travel support agent to maintain short-term and long-term customer memory while retrieving grounded company knowledge when needed.

The project includes:

Short-Term Memory

Scratchpad

Context Window Management

Promote-or-Drop Router

Router LLM

Episodic Memory

Semantic Memory

Memory Consolidation

Fact Extraction LLM

Vector Database

Naive RAG

Hybrid Search

Agentic RAG

Self-RAG Verification

End-to-End Agent Integration

The existing MCP Server and MySQL database are reused as the foundation of the system.

Problem Statement

Travel support conversations may contain large amounts of information, including:

Booking details

Flight information

Customer profiles

Refunds

Cancellations

Rebooking options

Company policies

Tool outputs

Keeping the entire conversation in the context window increases token usage and may cause important information to be lost.

The agent also needs access to company knowledge that is not directly available through MCP tools.

The goal is to provide the agent with:

Long-term memory of important customer information.

Grounded retrieval of company knowledge.

Overall Architecture

flowchart TD
    U[User] --> A[Travel Support Agent]

    A --> STM[Short-Term Memory]
    A --> RAG[RAG Retrieval]

    STM --> M[Messages]
    STM --> S[Scratchpad]
    STM --> C[Context Management]

    C --> R[Promote-or-Drop Router]

    R -->|DROP| D[Forget]
    R -->|PROMOTE| E[Episodic Memory]

    E --> CON[Consolidation Layer]
    CON --> SEM[Semantic Memory]
    SEM --> MR[Long-Term Memory Retrieval]

    RAG --> VS[Vector Search]
    RAG --> KS[Keyword / BM25 Search]
    RAG --> AR[Agentic RAG]

    VS --> RC[Retrieved Context]
    KS --> RC
    AR --> RC
    MR --> RC

    RC --> SR[Self-RAG Verification]
    SR --> FA[Final Answer]

Project Structure

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

Short-Term Memory

Short-Term Memory contains three separate structures.

Message Buffer

Stores the rolling conversation transcript.

Scratchpad

Stores information that must survive context pruning:

Current plan

Current sub-goal

Working state

High-stakes customer facts

MemoryItem Queue

Stores customer information waiting for the Promote-or-Drop Router.

flowchart TD
    STM[Short-Term Memory] --> MB[Messages]
    STM --> SP[Scratchpad]
    STM --> MI[MemoryItem Queue]

The scratchpad is injected into the agent prompt after context pruning so important information is never removed by the context strategy.

Context Window Management

The system implements four context management strategies:

Sliding Window

Observation / Tool Output Masking

Recursive Summarization

Zone-Based Pruning

Long-context conversations are evaluated using:

Task accuracy

Input tokens

Output tokens

Latency

The selected strategy is integrated into the live agent loop.

Promote-or-Drop Router

The router decides which MemoryItem should be retained.

flowchart TD
    MI[MemoryItem] --> RR[Rule-Based Router]

    RR -->|PROMOTE| E[Episodic Memory]
    RR -->|DROP| F[Forget]
    RR -->|UNKNOWN| LLM[Router LLM]

    LLM -->|PROMOTE| E
    LLM -->|DROP| F

Rules are evaluated first. The Router LLM is used only when the rules cannot determine the appropriate decision.

The router returns either:

PROMOTE + reason

or:

DROP + reason

The router only makes the decision between:

PROMOTE

DROP

It never writes directly to Semantic Memory.

The routing reason is logged for traceability.

Router LLM

The Router LLM is responsible only for deciding whether a memory item should be retained.

It is separate from the Fact Extractor LLM.

Router LLM
"What should I remember?"

Fact Extractor LLM
"What exactly is the persistent fact?"

This separation keeps memory routing and semantic fact extraction as independent responsibilities.

MemoryItem

MemoryItem connects customer messages to the memory pipeline.

MemoryItem(
    id=...,
    content=...,
    speaker="customer",
    timestamp=...,
    importance=...,
    metadata=...
)

Metadata can include:

entity_type
entity_id
turn
extraction_source

A MemoryItem can be created from a customer message and placed into the Short-Term Memory queue for routing.

Episodic Memory

Important customer events are stored as Episode objects.

Examples:

Booking confirmations

Booking cancellations

Refund requests

Customer preferences

Profile updates

Important travel events

An episode contains:

content
entity_type
entity_id
source
reason
created_at
metadata

The routing reason is preserved so promotion decisions remain explainable.

Semantic Memory

Semantic Memory stores persistent facts extracted from episodic memories.

Examples:

seat_preference → window
meal_preference → vegetarian
refund_preference → voucher

Semantic facts support:

Versioning

Expiration

Validity periods

Conflict resolution

Entity-based retrieval

Consolidation Layer

The Router does not write directly to Semantic Memory.

Instead, episodic memories are periodically consolidated.

flowchart TD
    E[Episodic Memory] --> C[Consolidation Layer]
    C --> R[Rule-Based Fact Extraction]

    R -->|Fact Found| SF[Semantic Fact]
    R -->|No Fact| LLM[Fact Extractor LLM]

    LLM --> SF
    SF --> SM[Semantic Memory]

The consolidation layer handles:

New facts

Updated facts

Contradictory facts

Fact versioning

Expiration

Historical validity

When a fact changes, the previous version is closed and a new version is created.

Fact Extractor LLM

The Fact Extractor LLM is responsible for extracting persistent semantic information from an episode.

It returns structured information containing:

is_fact
predicate
value
confidence

For example:

Customer prefers a window seat.
        ↓
predicate: seat_preference
value: window
confidence: 1.0

Rule-based extraction is attempted first, with the LLM used as a fallback.

High-Stakes Scratchpad Facts

The scratchpad detects important customer information that must remain available during the current conversation.

Examples include:

Accessibility requirements

Budget limits

Passport constraints

Refund preferences

Hard booking conditions

The detection pipeline is:

flowchart TD
    M[Customer Message] --> R[Rules]

    R -->|Found| P1[Pin Fact]
    R -->|Not Found| LLM[LLM]
    LLM --> P2[Pin Fact]

Each extracted fact can also be converted into a MemoryItem so it can participate in the long-term memory pipeline.

Memory Retrieval

Relevant semantic memories are retrieved for the current customer query.

flowchart LR
    Q[User Query] --> R[Semantic Memory Retrieval]
    R --> F[Relevant Customer Facts]
    F --> C[Agent Context]

This allows the agent to use information remembered from previous interactions.

Vector Database

The RAG system uses a vector database for semantic retrieval.

Each indexed document chunk contains:

Embedding
Original Text
Metadata

Metadata may include:

source
document type
section
date
entity

The vector index supports similarity-based retrieval and metadata filtering.

Document Processing Pipeline

flowchart TD
    D[Company Documents] --> C[Document Chunking]
    C --> E[Embeddings]
    E --> V[Vector Database]

    V --> VI[Vector Index]
    V --> MS[Metadata Store]
    V --> MI[Metadata Index]

The knowledge base contains company information such as:

Refund policies

Cancellation policies

VIP benefits

Travel voucher rules

Compensation policies

Airport information

Customer support policies

RAG Architectures

Naive RAG

flowchart LR
    Q[Query] --> E[Embedding]
    E --> VS[Vector Search]
    VS --> C[Retrieved Chunks]
    C --> LLM[LLM]
    LLM --> A[Answer]

Naive RAG provides the baseline retrieval approach.

Hybrid Search

Hybrid Search combines semantic and keyword retrieval.

flowchart TD
    Q[Query] --> V[Semantic Vector Search]
    Q --> K[Keyword / BM25 Search]

    V --> M[Merged Ranking]
    K --> M

    M --> C[Retrieved Context]

This is useful for exact information such as:

Booking codes

Flight numbers

Policy names

Exact business terms

Agentic RAG

Agentic RAG allows the agent to determine:

Whether retrieval is needed

What information should be retrieved

Whether another retrieval step is required

Whether the retrieved context is sufficient

flowchart TD
    Q[Question] --> AR[Agent Reasoning]
    AR --> R[Retrieve]
    R --> O[Observe Results]

    O -->|Sufficient| G[Generate]
    O -->|Insufficient| R

Retrieval Evaluation

The retrieval architectures are evaluated using the same domain-specific question set.

Evaluation metrics include:

Accuracy

Token usage per query

Latency per query

The test set includes:

General policy questions

Exact identifier questions

Multi-part questions

Questions requiring multiple retrieval steps

The final retrieval architecture is selected according to retrieval quality and measured performance.

Self-RAG Verification

The system verifies retrieval results and generated answers before returning them.

Retrieval Relevance

flowchart TD
    C[Retrieved Context] --> R{Is the context relevant?}

    R -->|Yes| G[Generate]
    R -->|No| X[Reject / Retry]

Answer Support

flowchart TD
    A[Generated Answer] --> S{Is the answer supported by evidence?}

    S -->|Yes| R[Return]
    S -->|No| G[Reject / Regenerate]

This reduces unsupported or ungrounded answers.

Self-RAG-style verification is applied to both retrieved company knowledge and long-term customer memory.

Agent Integration

Memory and retrieval are integrated directly into the live agent loop.

flowchart TD
    U[User Message] --> STM[Short-Term Memory]

    STM --> SP[Scratchpad]
    STM --> MI[MemoryItem]

    MI --> R[Promote-or-Drop Router]

    R -->|DROP| D[Forget]
    R -->|PROMOTE| E[Episodic Memory]

    E --> C[Consolidation]
    C --> SM[Semantic Memory]
    SM --> MR[Memory Retrieval]

    STM --> CM[Context Management]

    CM --> CTX[Agent Context]
    MR --> CTX
    RAG[RAG Retrieval] --> CTX

    CTX --> SR[Self-RAG Verification]
    SR --> AR[Agent Reasoning]
    AR --> MCP[MCP Tools]
    MCP --> FA[Final Answer]

The existing MCP Server and MySQL database remain responsible for live company data and business operations.

End-to-End Workflow

flowchart TD
    C[Conversation] --> STM[Short-Term Memory]
    STM --> CM[Context Management]
    CM --> R[Promote-or-Drop Router]

    R -->|DROP| D[Forget]
    R -->|PROMOTE| E[Episodic Memory]

    E --> CL[Consolidation Layer]
    CL --> SM[Semantic Memory]
    SM --> MR[Memory Retrieval]

    R2[RAG Retrieval] --> RC[Retrieved Context]
    MR --> RC

    RC --> SR[Self-RAG Verification]
    SR --> A[AI Agent]
    A --> MCP[MCP Tools]
    MCP --> UA[User Answer]

Testing

The project includes tests for:

Short-Term Memory

Scratchpad persistence

High-stakes fact extraction

MemoryItem creation

Promote-or-Drop routing

Episodic Memory

Semantic Memory

Consolidation

Fact versioning

Conflict resolution

Context window strategies

Vector retrieval

Naive RAG

Hybrid Search

Agentic RAG

Self-RAG verification

End-to-end agent integration

Run the tests with:

python -m pytest

Running the Project

1. Clone the Repository

git clone <repository-url>
cd WanderPathA

2. Install Dependencies

pip install -r requirements.txt

3. Configure Environment Variables

Create a .env file:

DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=travel_agency
GROQ_API_KEY=your_api_key

Never commit .env or API keys to GitHub.

Database Setup

Initialize the WanderPath database:

mysql < db/schema.sql
mysql < db/data.sql

The project reuses the existing database and MCP infrastructure.

Run the MCP Server

python server/server.py

Run the Agent

python agent/agent.py

Technologies

Python

MySQL

Model Context Protocol (MCP)

LangChain

Groq

Llama 3.3 70B

Pydantic

Embeddings

Vector Database

BM25

RAG

Agentic RAG

Self-RAG Verification

Approximate Nearest Neighbor Search

Security and Safety

The project maintains the security architecture of the original MCP Server.

No direct database access from the LLM

Server-side validation

Authorization checks

Controlled MCP tools

No raw SQL generated by the model

Environment variables for secrets

No committed API keys

Grounded RAG responses

Evidence verification

Explicit memory routing

Versioned semantic facts

Key Design Principles

Short-Term Memory and Scratchpad are separate.

Context pruning must never destroy the scratchpad.

The Router decides between forgetting and episodic promotion.

The Router does not write directly to Semantic Memory.

Semantic Memory is created through consolidation.

Contradictory facts are versioned instead of silently overwritten.

RAG answers are grounded in retrieved information.

Retrieval quality is evaluated using domain-specific questions.

Multiple retrieval architectures are evaluated.

The existing MCP Server and database are reused.

Project Result

The final system transforms WanderPath from an MCP-based travel support agent into a memory-aware and knowledge-grounded travel agent.

It can:

Maintain short-term conversational state

Preserve important customer information

Forget irrelevant information

Promote valuable memories to Episodic Memory

Consolidate episodes into Semantic Memory

Handle changing customer facts

Retrieve relevant long-term memories

Search company knowledge using semantic and keyword retrieval

Perform Naive, Hybrid, and Agentic RAG

Verify retrieved evidence before answering

Continue using the existing MCP tools and database

flowchart LR
    A[WanderPath MCP Agent]
    B[Short-Term Memory]
    C[Long-Term Memory]
    D[Vector Retrieval]
    E[RAG]
    F[Self-RAG Verification]
    G[Grounded Memory-Aware Travel Agent]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
