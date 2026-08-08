# Memory & RAG — Agent Memory System

## Overview

This task implements a multi-layer memory system for a travel-support Agent.

```text
User Message
     ↓
Short-Term Memory
     ↓
Promote-or-Drop Router
     ├── DROP
     └── PROMOTE
            ↓
      Episodic Memory
            ↓
     Consolidation Layer
            ↓
      Semantic Memory
            ↓
   Future Conversations
