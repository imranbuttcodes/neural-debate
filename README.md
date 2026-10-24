# AI Debate Arena

**Real-Time, Multi-Agent Debates Powered by Open-Weight LLMs, Live Web Citations, and Audience Voting.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white)](https://nextjs.org)
[![Groq](https://img.shields.io/badge/Groq-LPU_Inference-f55036)](https://groq.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_Workflow-blue)](https://langchain-ai.github.io/langgraph/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

**AI Debate Arena** is an interactive platform where two autonomous AI agents debate complex topics in front of a live audience. The debate takes place in real time with token-by-token streaming, factual grounding through live web search citations, and dynamic audience voting that allows viewers to switch their vote as arguments unfold.

### Agent Matchup
- **Agent A (Proponent):** `openai/gpt-oss-120b` — Focuses on broad rhetorical defense and logical structuring.
- **Agent B (Opponent):** `qwen/qwen3.8-27b` — Focuses on direct rebuttals, technical precision, and counter-evidence.

---

## System Architecture

```
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│       Creator Web Client        │                 │      Live Audience Viewers      │
│     (Topic, Tone, Timer)        │                 │    (Real-Time Voting & Chat)    │
└────────────────┬────────────────┘                 └────────────────▲────────────────┘
                 │                                                   │
                 │ HTTP POST /api/debates                            │ WebSocket
                 ▼                                                   ▼ /ws/debates/{id}
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                             FastAPI Application Server                              │
│                                                                                     │
│  ┌─────────────────────────┐   ┌──────────────────────────┐   ┌──────────────────┐  │
│  │   REST API Subsystem    │   │ WebSocket Hub & Broadcast│   │ SQLite / ORM     │  │
│  │  (Debates, Viewers,     │   │ (Tokens, Live Vote Split,│   │ (UPSERT Voting,  │  │
│  │   State Snapshots)      │   │  Room State Sync)        │   │  Rounds History) │  │
│  └─────────────┬───────────┘   └────────────▲─────────────┘   └────────┬─────────┘  │
└────────────────┼────────────────────────────┼──────────────────────────┼────────────┘
                 ▼                            │                          │
┌─────────────────────────────────────────────┴──────────────────────────▼────────────┐
│                             Autonomous Debate Engine                                │
│                                                                                     │
│   1. Web Search Node            2. Tone Synthesis           3. Groq LPU Streaming   │
│   (DuckDuckGo / Tavily)  ───>   (Prompt Assembly &   ───>   (Token chunks via       │
│                                  Opponent Context)           LangChain ChatGroq)    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Features

- **Token-by-Token Streaming:** Arguments stream directly from Groq LPUs through low-latency WebSockets directly into the client DOM.
- **Autonomous Evidence Retrieval:** Prior to each turn, agents formulate dynamic search queries and retrieve citations via DuckDuckGo (zero setup) or Tavily.
- **Contextual Memory & Direct Rebuttals:** Each debater receives the opponent's previous argument in its context window to formulate direct counter-arguments.
- **Dynamic Audience Voting (UPSERT):** Viewers can cast a vote and switch their choice at any point during the debate. Every change is immediately broadcast to all viewers with animated visual splits.
- **Late Joiner & Reconnect Synchronization:** Reconnecting clients and late joiners receive a complete `state_snapshot` payload restoring the full transcript history, timer, and current vote tally.
- **Four Distinct Debate Tones:**
  - `Roasting` — Sharp wit, satire, and incisive takedowns.
  - `Comedic` — Satirical analogies and humorous timing.
  - `Aggressive` — Assertive deconstruction of opposing assumptions.
  - `Devil's Advocate` — Contrarian interpretations and paradox exploration.

---

## Project Structure

```
neural-debate/
├── backend/
│   ├── app/
│   │   ├── main.py              # Application entrypoint, CORS, and WebSocket router
│   │   ├── db.py                # Database connection and session management
│   │   ├── models.py            # SQLAlchemy schema models
│   │   ├── schemas.py           # Pydantic v2 validation models
│   │   ├── crud.py              # Database access helpers and UPSERT vote logic
│   │   ├── websockets.py        # Connection manager and room broadcast logic
│   │   ├── agents/
│   │   │   ├── debate_graph.py  # Agent execution pipeline (Search -> LLM -> Citations)
│   │   │   ├── llm.py           # Groq LangChain client factory
│   │   │   ├── search.py        # DuckDuckGo and Tavily integration
│   │   │   ├── state.py         # Agent state schemas and memory structures
│   │   │   └── tones.py         # Tone-specific prompt templates
│   │   ├── routers/
│   │   │   ├── debate.py        # /api/debates endpoints and snapshot controller
│   │   │   ├── viewer.py        # /api/viewers registration endpoints
│   │   │   └── vote.py          # /api/votes casting and update endpoints
│   │   └── services/
│   │       └── debate_engine.py # Background round scheduling, timer, and voting windows
│   └── requirements.txt         # Pinned backend dependencies
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css      # Dark-mode design system and typography tokens
│   │   │   ├── layout.jsx       # Root layout and metadata configuration
│   │   │   ├── page.jsx         # Homepage and debate creation flow
│   │   │   └── join/[uuid]/     # Dynamic viewer lobby and arena state machine
│   │   ├── components/
│   │   │   ├── AgentPanel.jsx   # Streaming text display and transcript cards
│   │   │   ├── CitationCard.jsx # Formatted external evidence references
│   │   │   ├── CountdownTimer.jsx # Synchronized arena countdown bar
│   │   │   ├── CreateDebateForm.jsx # Parameter configuration and launch form
│   │   │   ├── DebateArena.jsx  # Main split-screen container
│   │   │   ├── LiveVoteBar.jsx  # Animated audience split visualization
│   │   │   ├── RoundBadge.jsx   # Stage and speaker turn indicator
│   │   │   ├── VoteSection.jsx  # Audience voting buttons and action triggers
│   │   │   ├── WaitingRoom.jsx  # Pre-debate holding lobby
│   │   │   └── WinnerScreen.jsx # Concluding results and vote breakdown
│   │   └── lib/
│   │       ├── api.js           # REST API client
│   │       └── ws.js            # WebSocket client with auto-reconnection
│   └── package.json             # Next.js 14 and React dependencies
│
├── .env.example                 # Environment configuration template
└── README.md                    # Project documentation
```

---

## Environment Configuration

Copy `.env.example` to `.env` in the repository root and configure the necessary keys:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | **Yes** | — | API key from [Groq Console](https://console.groq.com) |
| `GROQ_MODEL_A` | No | `openai/gpt-oss-120b` | Model identifier for Debater A |
| `GROQ_MODEL_B` | No | `qwen/qwen3.8-27b` | Model identifier for Debater B |
| `GROQ_TIMEOUT` | No | `30` | Timeout in seconds for LLM inferences |
| `TAVILY_API_KEY` | No | — | Optional search fallback key |
| `SEARCH_MAX_RESULTS`| No | `3` | Maximum search citations per argument turn |
| `DATABASE_URL` | No | `sqlite:///./debate.db` | SQLAlchemy connection string |
| `DEBATE_MAX_DURATION` | No | `300` | Maximum debate time cap in seconds |
| `VOTING_WINDOW_SECS` | No | `15` | Window duration following each turn |
| `FRONTEND_URL` | No | `http://localhost:3000` | Allowed CORS origin and invite base URL |
| `PORT` | No | `8000` | Backend API port |

---

## Installation & Running

### Prerequisites
- Python 3.11+
- Node.js 18.0+
- `uv` (recommended) or `pip`
- A free API key from [Groq](https://console.groq.com)

### 1. Backend Setup

```bash
# Create virtual environment at root and install dependencies
uv venv .venv
source .venv/bin/activate
uv pip install -r backend/requirements.txt

# Start the FastAPI server (from repository root or backend directory)
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **API Root:** `http://localhost:8000`
- **Swagger Documentation:** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`

### 2. Frontend Setup

```bash
cd frontend

# Install package dependencies
npm install

# Build and run production bundle
npm run build
npm run start

# Alternatively, run development mode:
# npm run dev
```

- **Frontend Interface:** `http://localhost:3000`

---

## REST API Reference

| Method | Endpoint | Headers / Auth | Description |
|---|---|---|---|
| `POST` | `/api/debates` | None | Create a new debate and generate an invite link |
| `GET` | `/api/debates/{id}` | None | Retrieve debate metadata and current status |
| `GET` | `/api/debates/{id}/state` | Optional `X-Viewer-Id` | Full snapshot (history, timer, vote counts, viewer vote) |
| `GET` | `/api/debates/invite/{uuid}`| None | Resolve invite link into debate parameters for viewers |
| `POST` | `/api/debates/{id}/start` | `X-Creator-Token: <token>` | Start debate engine ticker and round lifecycle |
| `POST` | `/api/viewers` | None | Register viewer display name and avatar |
| `GET` | `/api/viewers/debate/{id}` | None | List currently active viewers in the arena |
| `POST` | `/api/votes` | `X-Viewer-Id: <uuid>` | Cast a vote (`A` or `B`) |
| `PATCH`| `/api/votes` | `X-Viewer-Id: <uuid>` | Update/switch an existing vote |
| `GET` | `/api/votes/{debate_id}` | None | Fetch aggregated vote counts and percentage splits |

---

## WebSocket Protocol

WebSocket connection endpoint:
```
ws://localhost:8000/ws/debates/{debate_id}?viewer_id={viewer_id}
```

### Event Payloads Broadcast by Server

- **`state_snapshot`**: Sent immediately upon connection to initialize past rounds, votes, and time.
- **`round_start`**: Signals the start of a round (`Opening`, `Rebuttal`, `Closing`) and indicates the active speaker.
- **`agent_thinking`**: Emitted while the agent queries the search engine and synthesizes its argument.
- **`argument_token`**: High-frequency streaming chunks pushed token-by-token directly to client text views.
- **`argument_done`**: Signals completion of argument delivery and contains full citation metadata.
- **`voting_open` / `voting_closed`**: Controls audience voting window state.
- **`live_vote_update`**: Pushed instantly upon any audience vote or change (`A`, `B`, `total`, `percent_A`, `percent_B`).
- **`timer_tick`**: Emitted every second with remaining duration.
- **`finished`**: Concludes the debate, announces the winner, and delivers the full round breakdown.

---

## Testing via cURL

```bash
# 1. Create a debate
DEBATE=$(curl -s -X POST http://localhost:8000/api/debates \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Microservices vs Monoliths",
    "tone": "roasting",
    "duration_secs": 180
  }')
echo $DEBATE

# 2. Extract Debate ID and Creator Token
DEBATE_ID=$(echo $DEBATE | python3 -c "import sys, json; print(json.load(sys.stdin)['debate_id'])")
TOKEN=$(echo $DEBATE | python3 -c "import sys, json; print(json.load(sys.stdin)['creator_token'])")

# 3. Register a viewer
VIEWER=$(curl -s -X POST http://localhost:8000/api/viewers \
  -H "Content-Type: application/json" \
  -d "{\"debate_id\": $DEBATE_ID, \"display_name\": \"Alex\", \"avatar_emoji\": \"🦊\"}")
VIEWER_ID=$(echo $VIEWER | python3 -c "import sys, json; print(json.load(sys.stdin)['viewer_id'])")

# 4. Cast and switch vote
curl -X PATCH http://localhost:8000/api/votes \
  -H "Content-Type: application/json" \
  -H "X-Viewer-Id: $VIEWER_ID" \
  -d "{\"debate_id\": $DEBATE_ID, \"vote\": \"A\"}"

# 5. Start the debate
curl -X POST http://localhost:8000/api/debates/$DEBATE_ID/start \
  -H "X-Creator-Token: $TOKEN"
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
