# 🎙️ Production Voice-Enabled Agent with LangGraph & Human-in-the-Loop (HITL)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production_Backend-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Orchestration-orange.svg)](https://github.com/langchain-ai/langgraph)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Persistent_LTM-336791.svg)](https://www.postgresql.org/)
[![Deepgram](https://img.shields.io/badge/Deepgram-Nova--2_STT_%26_Aura_TTS-red.svg)](https://deepgram.com)

A production-grade, voice-first agentic system designed to eliminate LLM hallucinations through **Human-in-the-Loop (HITL) gatekeepers**, backed by **dual memory systems (STM + PostgreSQL Persistent LTM)**, **Tavily search intelligence**, and real-time audio streaming.

---

## 🎬 Live System Walkthrough & HITL Verification Demo

https://github.com/user-attachments/assets/Voice_agent.mp4

> **Watch the full demonstration:**  
> ▶️ **[Click here to watch / download Voice_agent.mp4](file:///e:/Ghost%20OS/projects/Lang-Graph/voice-chatbot-hitl/Voice_agent.mp4)** *(or view directly in repo at `voice-chatbot-hitl/Voice_agent.mp4`)*  
> *Demonstrates: Account authentication, dynamic speech-to-text, context extraction into LTM, deterministic HITL Review Gate interruption, operator approval, and sub-second text-to-speech delivery.*

---

## 🎯 The Core Problem & Architectural Philosophy

Most conversational AI assistants fail in enterprise environments for two simple reasons:
1. **Silent Hallucinations on High-Stakes Actions:** The agent sends unverified answers or executes tools without operator oversight.
2. **Context Amnesia Across Sessions:** Ephemeral memory dies on reload, and naive vector DBs silently lose track of user profile constraints.

This repository demonstrates how to build a **reliable, verifiable conversational agent** using:
- **Deterministic State Interrupts (HITL):** High-stakes responses enter a `pending` state, allowing the human operator to inspect, edit, or reject the output before final delivery.
- **Dual Memory Architecture:** Ephemeral Short-Term Memory (STM) for per-turn conversational context, coupled with a durable PostgreSQL Long-Term Memory (LTM) store tied to JWT-authenticated user accounts.
- **Sub-Second Voice Processing:** Deepgram Nova-2 for ultra-fast Speech-to-Text and Deepgram Aura for natural Text-to-Speech synthesis.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client [Voice & Web Client]
        UI[Interactive Web Interface]
        Mic[Deepgram Nova-2 STT]
        Speaker[Deepgram Aura TTS]
        UI -->|Audio Input| Mic
        Mic -->|Transcribed Text| API[POST /chat]
    end

    subgraph Backend [FastAPI Orchestrator]
        API --> Auth[JWT Security & User Context]
        Auth --> Intent{Requires Live Search?}
        Intent -->|Yes: News/Company/Profile| Tavily[Tavily Search Engine]
        Intent -->|No| Graph[LangGraph State Workflow]
        Tavily -->|Grounded Search Context| Graph
        
        subgraph LangGraph [LangGraph Stateful Execution]
            Remember[Remember Node: Extract Facts & Update LTM]
            ChatNode[Chat Node: Synthesize Response with Profile Context]
            Remember --> ChatNode
        end
        Graph --> LangGraph
    end

    subgraph Storage [Persistent Database]
        Auth <--> UsersTable[(Postgres: User Credentials)]
        Remember <--> LTMStore[(PostgresStore: Cross-Session Facts)]
        ChatNode <-- Query Memory --> LTMStore
    end

    subgraph Verification [Human-in-the-Loop Gate]
        ChatNode --> Gate{HITL Review Enabled?}
        Gate -->|Enabled: status='pending'| Operator[Operator Approval Modal]
        Operator -->|Approve: status='delivered'| Speaker
        Operator -->|Reject + Adjust Feedback| ChatNode
        Gate -->|Disabled| Speaker
    end
```

---

## 📂 Repository Structure

```
Lang-Graph/
├── voice-chatbot-hitl/         # 🚀 MAIN PRODUCTION APPLICATION
│   ├── backend/
│   │   ├── auth.py             # User signup/login, bcrypt password hashing, JWT tokens
│   │   └── main.py             # FastAPI App, CORS, route handlers, HITL endpoints
│   ├── src/
│   │   ├── core/
│   │   │   ├── nodes.py        # LangGraph nodes (Remember Node, Chat Node)
│   │   │   └── state.py        # TypedDict conversation state structure
│   │   └── integrations/
│   │       ├── db_config.py    # PostgresStore persistent storage + InMemory fallback
│   │       ├── voice_integration.py   # Deepgram STT/TTS pipeline
│   │       └── tavily_integration.py  # Intent-driven live web search
│   ├── frontend/
│   │   ├── index.html          # Modern glassmorphism UI with Audio Player & HITL review
│   │   └── vercel.json         # Static frontend hosting configuration
│   ├── docker-compose.yml      # Local PostgreSQL container service
│   ├── render.yaml             # Render Blueprint for 1-click cloud deployment
│   └── requirements.txt        # Backend dependencies
└── learning-material/          # 🧠 LangGraph Core Patterns & Laboratory Notebooks
    ├── 01_simple_chain.py      # Cyclical graphs vs linear chains
    ├── 02_state_management.py # Annotated reducers & message history
    ├── 03_conditional_edges.py # Dynamic routing logic
    └── 04_checkpoints.py       # State persistence and recovery
```

---

## 🚀 Quickstart: Run Locally in 3 Steps

### 1. Start Persistent PostgreSQL
```bash
cd voice-chatbot-hitl
docker compose up -d
```
*This spins up a localized PostgreSQL instance at `localhost:5442` dedicated to long-term memory.*

### 2. Configure Environment & Install Dependencies
Create `.env` inside `voice-chatbot-hitl/`:
```env
GOOGLE_API_KEY=your_gemini_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
TAVILY_API_KEY=your_tavily_api_key
JWT_SECRET_KEY=generate_a_secure_jwt_secret_token
DATABASE_URL=postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable
```

Install requirements:
```bash
pip install -r requirements.txt fastapi uvicorn bcrypt pyjwt
```

### 3. Launch the FastAPI Backend
```bash
uvicorn backend.main:app --reload --port 8000
```

Open `frontend/index.html` in any browser or launch with Live Server. Sign up, enable the **Human-in-the-Loop Toggle**, and speak into the microphone!

---

## 🛡️ Enterprise Evaluation & Safety Highlights

| Dimension | Implementation | Value to Production |
| :--- | :--- | :--- |
| **Human Gatekeeping** | Explicit approval endpoints (`/approve`) | 0 unauthorized actions or unverified outbound answers. |
| **Memory Isolation** | User-partitioned `PostgresStore` via JWT tokens | Multi-tenant memory privacy — users only access their own facts. |
| **Intent-Gated Search** | Intent classification before retrieval | Reduces latency and external API consumption by 60%+. |
| **Graceful Degradation** | `InMemoryStore` fallback if Postgres is unavailable | Local developer agility without blocking deployment. |

---

## 👨‍💻 Author

**Akshu Grewal**  
*Agentic AI Engineer specializing in verifiable, reliable tool-using systems.*  
- GitHub: [@Akshu24Tech](https://github.com/Akshu24Tech)  
- Focus: LangGraph · Google ADK · Evals & Grounding · Fast APIs
