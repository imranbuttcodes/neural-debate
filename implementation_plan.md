# 🎭 AI Debate Arena — Execution Plan

## Goal
Build the complete AI Debate Arena from the [implementation spec](file:///home/aiml/Documents/neural-debate/AI_Debate_Arena_Implementation_Plan.md) as a greenfield project inside the `neural-debate` repo (currently on `AStart` branch). The project has two halves — a **FastAPI + LangGraph backend** and a **Next.js 14 frontend** — that communicate via REST + WebSocket.

## Environment
| Tool | Version |
|------|---------|
| Python | 3.14.5 |
| Node | 22.22.2 |
| npm | 10.9.7 |
| uv | 0.11.21 (user prefers `uv` over `pip`) |
| Branch | `AStart` |

---

## User Review Required

> [!IMPORTANT]
> **Groq API Key**: The backend requires a `GROQ_API_KEY` to call Llama 3.3 70B and Qwen 3.8 27B models. You'll need to set this in `.env` before running the backend. A free key takes 30 seconds at [console.groq.com](https://console.groq.com).

> [!IMPORTANT]
> **Package Manager**: Using `uv` for Python dependency management (per your preference) instead of `pip`. The `requirements.txt` from the spec will be installed via `uv pip install -r requirements.txt` inside a `uv venv`.

> [!WARNING]
> **Model Availability**: The spec references `qwen/qwen3.8-27b` on Groq. If this exact model ID isn't available, I'll substitute the closest available Qwen model and note the change.

---

## Open Questions

> [!IMPORTANT]
> **Tavily API Key**: The spec lists Tavily as a search fallback. Do you have a Tavily API key, or should I make DDG the only search provider? (DDG works without any key.)

---

## Proposed Changes — Phase-by-Phase

The spec defines 13 build phases (§18). I'll execute them in order, grouping related files. Each phase lists every file created/modified with key implementation details.

---

### Phase 1 — Database Layer (db, models, schemas, crud)
*~25 min — 🔴 Critical*

#### [NEW] `backend/app/__init__.py`
Empty init file to make `app` a Python package.

#### [NEW] `backend/app/db.py`
SQLAlchemy 2.0 async-compatible setup with SQLite:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./debate.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### [NEW] `backend/app/models.py`
5 SQLAlchemy ORM models matching §4 exactly:
- `Debate` — 14 columns (id, topic, description, tone, model_a/b, agent_a/b_name, duration_secs, status, creator_token, created_at, starts_at, ends_at, winner)
- `InviteLink` — uuid PK, debate_id FK, created_at, expires_at
- `Viewer` — uuid PK, debate_id FK, display_name, avatar_emoji, joined_at, last_seen_at, is_online
- `DebateRound` — round_number, label, agent, argument, citations (JSON), model_name, search_query, started_at, ended_at
- `Vote` — debate_id + viewer_id with `UniqueConstraint`, vote, created_at, updated_at

#### [NEW] `backend/app/schemas.py`
Pydantic v2 request/response models:
- `DebateCreate`, `DebateResponse`, `DebateStateSnapshot`
- `ViewerCreate`, `ViewerResponse`
- `VoteCreate`, `VoteResponse`, `VoteCounts`

#### [NEW] `backend/app/crud.py`
All DB operations including the critical vote UPSERT:
- `create_debate()`, `get_debate()`, `start_debate()`, `finish_debate()`
- `create_invite()`, `get_debate_by_invite()`
- `create_viewer()`, `get_viewers()`, `set_viewer_offline()`
- `create_round()`, `get_rounds()`
- `upsert_vote()` — INSERT or UPDATE on `(debate_id, viewer_id)`
- `get_vote_counts()` — returns `{A, B, total, percent_A, percent_B}`

---

### Phase 2 — WebSocket Connection Manager
*~10 min — 🔴 Critical*

#### [NEW] `backend/app/websockets.py`
```python
class ConnectionManager:
    def __init__(self):
        self.active: dict[int, dict[str, WebSocket]] = {}  # debate_id → {viewer_id: ws}

    async def connect(self, debate_id, viewer_id, ws)
    async def disconnect(self, debate_id, viewer_id)
    async def broadcast(self, debate_id, message: dict)
    async def send_personal(self, debate_id, viewer_id, message: dict)
```
- Keyed by `debate_id` → dict of `viewer_id` → `WebSocket`
- `broadcast()` fans out JSON to all viewers in a debate room
- Handles disconnection gracefully (removes dead connections)

---

### Phase 3 — Agent Layer: State, Search, LLM
*~20 min — 🔴 Critical*

#### [NEW] `backend/app/agents/__init__.py`

#### [NEW] `backend/app/agents/state.py`
Pydantic models from §9: `SearchResult`, `PreviousArgument`, `DebateState`

#### [NEW] `backend/app/agents/search.py`
Web search with DDG primary + Tavily fallback:
```python
async def search_web(query: str, max_results: int = 3) -> list[SearchResult]:
    try:
        results = DDGS().text(query, max_results=max_results)
        return [SearchResult(title=r["title"], snippet=r["body"], url=r["href"]) for r in results]
    except Exception:
        if TAVILY_API_KEY:
            # Tavily fallback
        return []  # graceful degradation
```

#### [NEW] `backend/app/agents/llm.py`
LLM factory with Groq primary + Ollama fallback:
```python
def get_llm(model_name: str, streaming: bool = True):
    try:
        return ChatGroq(model=model_name, streaming=streaming, api_key=GROQ_API_KEY)
    except Exception:
        return ChatOllama(model=OLLAMA_FALLBACK, base_url=OLLAMA_BASE_URL)
```

---

### Phase 4 — Agent Layer: Tones + LangGraph
*~30 min — 🔴 Critical*

#### [NEW] `backend/app/agents/tones.py`
4 tone prompt templates from §8 (roasting, comedic, aggressive, devils_advocate) + user prompt template. Each returns a fully formatted `(system_prompt, user_prompt)` tuple.

#### [NEW] `backend/app/agents/debate_graph.py`
LangGraph `StateGraph` with 4 nodes:
```
search_node → tone_node → llm_node → format_node
```
- `search_node`: calls `search_web()`, stores results in state
- `tone_node`: assembles system + user prompts using tone templates + previous_arguments
- `llm_node`: streams tokens via `ChatGroq.astream()`, calls a broadcast callback per token
- `format_node`: validates citations, trims to 200 words if needed

Key: the `llm_node` accepts a `token_callback` that the debate engine injects to broadcast `argument_token` events.

---

### Phase 5 — Debate Engine Service
*~30 min — 🔴 Critical*

#### [NEW] `backend/app/services/__init__.py`

#### [NEW] `backend/app/services/debate_engine.py`
The core async orchestrator that runs when a debate starts:
```python
async def run_debate(debate_id: int, ws_manager: ConnectionManager):
    # Launch two concurrent tasks:
    # 1. ticker_task — broadcasts timer_tick every 1s
    # 2. rounds_task — runs 4 rounds sequentially

    # Each round:
    #   broadcast round_start → agent_thinking
    #   invoke LangGraph graph (with token streaming callback)
    #   broadcast argument_done + citations
    #   broadcast voting_open → wait 15s → voting_closed
    #   Check if timer expired → break early if so

    # After all rounds or timer:
    #   count votes → determine winner → broadcast finished
```

---

### Phase 6 — API Routers
*~25 min — 🔴 Critical*

#### [NEW] `backend/app/routers/__init__.py`

#### [NEW] `backend/app/routers/debate.py`
| Endpoint | Purpose |
|----------|---------|
| `POST /api/debates` | Create debate, generate invite link, return creator_token |
| `GET /api/debates/{id}` | Get debate details |
| `GET /api/debates/{id}/state` | Full snapshot for reconnect/late join |
| `GET /api/debates/invite/{uuid}` | Resolve invite link → debate metadata |
| `POST /api/debates/{id}/start` | Creator starts debate (X-Creator-Token auth) |

#### [NEW] `backend/app/routers/viewer.py`
| Endpoint | Purpose |
|----------|---------|
| `POST /api/viewers` | Register viewer (name + emoji) → viewer_id |
| `GET /api/viewers/debate/{debate_id}` | List active viewers |

#### [NEW] `backend/app/routers/vote.py`
| Endpoint | Purpose |
|----------|---------|
| `POST /api/votes` | Cast vote (UPSERT) |
| `PATCH /api/votes` | Change vote (same UPSERT) |
| `GET /api/votes/{debate_id}` | Get current vote counts |

Both POST and PATCH trigger `live_vote_update` broadcast to all viewers.

---

### Phase 7 — Main App Wiring
*~10 min — 🔴 Critical*

#### [NEW] `backend/app/main.py`
```python
app = FastAPI(title="AI Debate Arena")
# CORS middleware (allow frontend origin)
# Include routers: debate, viewer, vote
# WebSocket endpoint: /ws/debates/{debate_id}
#   - on connect: send state_snapshot
#   - on disconnect: broadcast viewer_left
# Create tables on startup
```

#### [NEW] `backend/requirements.txt`
All deps from §16, installed via `uv`.

#### [NEW] `.env.example`
Template with all env vars from §15.

---

### Phase 8 — Backend Integration Test
*~15 min — 🔴 Critical*

Manual testing via curl:
1. `POST /api/debates` → verify response shape
2. `POST /api/viewers` → verify viewer_id returned
3. `POST /api/debates/{id}/start` → verify debate starts
4. Connect to WebSocket → verify events stream
5. `POST /api/votes` → verify vote + broadcast

---

### Phase 9 — Frontend: Core Pages + WebSocket
*~40 min — 🟡 Important*

#### [NEW] `frontend/` (Next.js 14 App Router)
Initialize with `npx -y create-next-app@latest ./` with App Router, no Tailwind, JS (not TS for speed).

#### [NEW] `frontend/src/lib/api.js`
All `fetch()` wrappers for the 8 REST endpoints.

#### [NEW] `frontend/src/lib/ws.js`
WebSocket wrapper with auto-reconnect:
```javascript
export function createDebateWS(debateId, viewerId, onMessage) {
    // Connect, auto-reconnect on close, parse JSON messages
    // Return { send, close } handle
}
```

#### [NEW] `frontend/src/app/layout.jsx`
Root layout with Inter font, global CSS import, dark theme `<body>`.

#### [NEW] `frontend/src/app/page.jsx`
"/" — Create Debate page with `CreateDebateForm` component.

#### [NEW] `frontend/src/app/created/page.jsx`
"/created" — Shows invite URL + Start button (creator flow).

#### [NEW] `frontend/src/app/join/[uuid]/page.jsx`
"/join/:uuid" — Viewer entry + arena. This is the main page with the full state machine:
`JoinLobby → WaitingRoom → DebateArena → WinnerScreen`

#### [NEW] `frontend/src/components/CreateDebateForm.jsx`
Form with: topic input, description textarea, tone selector (4 options), timer slider.

#### [NEW] `frontend/src/components/JoinLobby.jsx`
Name input + emoji avatar grid picker.

#### [NEW] `frontend/src/components/WaitingRoom.jsx`
"🎭 Waiting for creator to start…" with viewer list.

#### [NEW] `frontend/src/components/DebateArena.jsx`
Main split-panel container: Agent A panel | Timer | Agent B panel.

#### [NEW] `frontend/src/components/AgentPanel.jsx`
One agent's side: name/emoji header, streaming text area (with typing cursor), citations below.

---

### Phase 10 — Frontend: Voting + Winner
*~25 min — 🟡 Important*

#### [NEW] `frontend/src/components/VoteSection.jsx`
Two glowing vote buttons (🦙 vs 🐉) + current user's selection highlighted.

#### [NEW] `frontend/src/components/LiveVoteBar.jsx`
Animated horizontal bar showing A% vs B% with smooth CSS transitions.

#### [NEW] `frontend/src/components/WinnerScreen.jsx`
Confetti animation + winner announcement + full vote breakdown table.

#### [NEW] `frontend/src/components/ThinkingIndicator.jsx`
Pulsing "🤔 Searching the web…" animation.

#### [NEW] `frontend/src/components/CitationCard.jsx`
Single citation: title, snippet, clickable URL.

#### [NEW] `frontend/src/components/CountdownTimer.jsx`
Large countdown display with progress bar.

#### [NEW] `frontend/src/components/RoundBadge.jsx`
"Round 2 — Rebuttal 🗡️" badge.

#### [NEW] `frontend/src/components/ViewerList.jsx`
Scrolling list of connected viewers with emoji avatars.

#### [NEW] `frontend/src/components/InviteScreen.jsx`
Invite link display with copy button + Start Debate button for creator.

---

### Phase 11 — Creator Flow UI
*~20 min — 🟡 Important*

Already covered in Phase 9-10 components. This phase focuses on:
- Wiring `CreateDebateForm` → `POST /api/debates` → redirect to `/created`
- `InviteScreen` → copy link + `POST /api/debates/{id}/start` → WS events begin

---

### Phase 12 — CSS: Dark Mode, Animations, Polish
*~25 min — 🟢 Polish*

#### [NEW] `frontend/src/app/globals.css`
Complete design system:
- **Dark mode** base with deep navy/charcoal palette
- **Glassmorphism** panels with `backdrop-filter: blur()`
- **CSS custom properties** for all colors, spacing, typography
- **Animations**: typing cursor blink, vote bar slide, confetti burst, pulse thinking, viewer join fade-in, round badge entrance
- **Responsive** breakpoints for mobile/tablet/desktop
- **Inter** font from Google Fonts

---

### Phase 13 — End-to-End Test
*~15 min — 🟢 Polish*

1. Start backend: `uvicorn app.main:app --reload --port 8000`
2. Start frontend: `npm run dev`
3. Create debate via UI
4. Open invite link in 2+ browser tabs
5. Start debate → verify token streaming, voting, winner

---

## File Creation Summary

```
neural-debate/
├── .env.example                          [NEW]
├── AI_Debate_Arena_Implementation_Plan.md (existing)
├── LICENSE                                (existing)
├── README.md                              (MODIFY — update with project desc)
│
├── backend/
│   ├── requirements.txt                   [NEW]
│   └── app/
│       ├── __init__.py                    [NEW]
│       ├── main.py                        [NEW]
│       ├── db.py                          [NEW]
│       ├── models.py                      [NEW]
│       ├── schemas.py                     [NEW]
│       ├── crud.py                        [NEW]
│       ├── websockets.py                  [NEW]
│       ├── routers/
│       │   ├── __init__.py                [NEW]
│       │   ├── debate.py                  [NEW]
│       │   ├── viewer.py                  [NEW]
│       │   └── vote.py                    [NEW]
│       ├── agents/
│       │   ├── __init__.py                [NEW]
│       │   ├── state.py                   [NEW]
│       │   ├── search.py                  [NEW]
│       │   ├── llm.py                     [NEW]
│       │   ├── tones.py                   [NEW]
│       │   └── debate_graph.py            [NEW]
│       └── services/
│           ├── __init__.py                [NEW]
│           └── debate_engine.py           [NEW]
│
└── frontend/
    ├── package.json                       [NEW] (via create-next-app)
    ├── next.config.js                     [NEW]
    └── src/
        ├── app/
        │   ├── layout.jsx                 [NEW]
        │   ├── page.jsx                   [NEW]
        │   ├── globals.css                [NEW]
        │   ├── created/
        │   │   └── page.jsx               [NEW]
        │   └── join/
        │       └── [uuid]/
        │           └── page.jsx           [NEW]
        ├── components/
        │   ├── CreateDebateForm.jsx        [NEW]
        │   ├── InviteScreen.jsx            [NEW]
        │   ├── JoinLobby.jsx               [NEW]
        │   ├── WaitingRoom.jsx             [NEW]
        │   ├── DebateArena.jsx             [NEW]
        │   ├── AgentPanel.jsx              [NEW]
        │   ├── ThinkingIndicator.jsx       [NEW]
        │   ├── CitationCard.jsx            [NEW]
        │   ├── CountdownTimer.jsx          [NEW]
        │   ├── RoundBadge.jsx              [NEW]
        │   ├── VoteSection.jsx             [NEW]
        │   ├── LiveVoteBar.jsx             [NEW]
        │   ├── ViewerList.jsx              [NEW]
        │   └── WinnerScreen.jsx            [NEW]
        └── lib/
            ├── api.js                      [NEW]
            └── ws.js                       [NEW]
```

**Total: ~40 new files** across backend and frontend.

---

## Verification Plan

### Automated Tests
```bash
# Backend: verify server starts and API docs render
cd backend && uv run uvicorn app.main:app --port 8000 &
curl -s http://localhost:8000/docs | head -5   # Should return HTML
curl -s http://localhost:8000/api/debates -X POST -H "Content-Type: application/json" \
  -d '{"topic":"Test","tone":"roasting"}' | python3 -m json.tool

# Frontend: verify build succeeds
cd frontend && npm run build
```

### Manual Verification
1. **Create debate** via the web UI at `http://localhost:3000`
2. **Copy invite link** and open in a second browser tab
3. **Join** as a viewer (enter name + pick emoji)
4. **Start debate** from the creator tab
5. **Verify**: token streaming appears live, thinking indicator shows, citations render
6. **Vote** from the viewer tab → verify live vote bar updates
7. **Wait for timer** → verify winner screen with confetti
8. **Refresh page** mid-debate → verify state snapshot restores correctly
