# 🎭 AI Debate Arena — Full Implementation Plan v2.0

> **Hackathon:** Hacktoberfest Hack Day Lahore × Cloud Native Security Pakistan
> **Prize:** Best Open-Source AI Project
> **Deadline:** Oct 24, 2026 — 5:00 PM PKT
> **Version:** 2.0 — All critical gaps fixed ✅

---

## ⚠️ What Was Wrong in v1 (Gap Audit)

| # | Gap | Impact | Fix in v2 |
|---|-----|--------|-----------|
| 1 | No token-by-token streaming | Argument appears all at once, not live | Groq streaming + `argument_token` WS event |
| 2 | Vote can't be changed | `UNIQUE` constraint BLOCKS re-voting | UPSERT on `(debate_id, viewer_id)` + `PATCH /api/votes` |
| 3 | No live vote count push | Vote count only updates on page refresh | Every vote triggers broadcast to ALL viewers |
| 4 | Agent has no "thinking" state | UI freezes while agent searches + generates | `agent_thinking` WS event before generation starts |
| 5 | No emojis in tone prompts | Arguments are dry, not entertaining | Explicit emoji instructions in every tone prompt |
| 6 | Agents don't see opponent's argument | Rebuttal is generic, not a real counter | `previous_arguments` list passed into LangGraph state |
| 7 | No `round_label` (Opening/Rebuttal/Closing) | UI can't label what type of argument it is | Added to DB + WS events |
| 8 | No viewer reconnect logic | Page refresh = lost state, no replay | Snapshot API + replay-on-connect |
| 9 | No debate snapshot endpoint | Late joiners see blank screen | `GET /api/debates/{id}/state` returns full current state |
| 10 | No `PATCH /api/votes` | Users can't change their mind | New endpoint, UPSERT DB logic |
| 11 | Agent nicknames not defined | UI shows raw model ID strings | Named agents: 🦙 Llama vs 🐉 Qwen |
| 12 | No `argument_token` WS event | Can't stream tokens char-by-char | New streaming event type added |
| 13 | No `round_start` WS event | UI doesn't know a new round began | New event, triggers round header in UI |
| 14 | No `voting_open`/`voting_closed` events | Vote buttons show/hide randomly | Explicit events control vote button visibility |
| 15 | No error/fallback WS event | If Groq fails, UI silently freezes | `agent_error` event with retry logic |
| 16 | No viewer leave/count update | Viewer count shown is stale | `viewer_left` WS event |
| 17 | One vote per ROUND not defined | Old schema had votes per round, confusing | One global vote per debate (changeable any time) |
| 18 | Frontend state machine undefined | Unclear how UI transitions between states | Complete state diagram added |
| 19 | `DebateState` missing history | LangGraph doesn't carry conversation memory | `previous_arguments` field added |
| 20 | Missing `agent_done` event | UI doesn't know when streaming is complete | `argument_done` event ends typing animation |

---

## 1. 🧠 Project Idea

**AI Debate Arena** is a real-time, audience-powered debate platform where two
open-weight AI agents (🦙 Llama 3.3 70B vs 🐉 Qwen 3.8 27B) argue any topic
chosen by a human — while a live audience watches, reacts, and votes **in real time**.

### Core Experience
1. **Creator** enters topic, description, tone, and timer from a web form or terminal.
2. System generates a **shareable invite link** — no sign-up for viewers.
3. Viewers enter their name + pick a fun emoji avatar.
4. Creator presses **START** — debate begins immediately.
5. Agents take turns, **token by token** (like watching someone type live).
6. Before each turn, agents **search the web** for real evidence and cite it.
7. Agents **remember what the opponent said** — rebuttals are actual counters.
8. Viewers can **vote for either agent at any time** and **change their vote freely** 
   during the debate. Live vote counts pulse on screen.
9. After the timer ends, **winner is declared by total votes** with confetti.

### What Makes It Entertaining
- 🎭 Tone modes: **Roasting**, **Comedic**, **Aggressive**, **Devil's Advocate**
- 🔥 Arguments include **emojis, sarcasm, and real citations**
- 📊 **Live vote bars** animate every time anyone votes or changes vote
- 👥 **Viewer join notifications** pop up in real-time ("🦊 Ali joined!")
- ⏱️ **Countdown timer** creates urgency
- 🏆 **Winner reveal** with confetti and full vote breakdown

---

## 2. 📋 Complete Feature List

| # | Feature | Who | MVP/v2 |
|---|---------|-----|--------|
| 1 | Create debate: topic, desc, tone, timer, model pick | Creator | MVP |
| 2 | Generate shareable invite link (UUID, no auth) | System | MVP |
| 3 | Join via link: enter name + pick emoji avatar | Viewer | MVP |
| 4 | Viewer ID generated + stored in localStorage | System | MVP |
| 5 | Live viewer count + join notifications in UI | System | MVP |
| 6 | Token-by-token streaming of agent arguments | System | MVP |
| 7 | Agent searches web before each turn | Agent | MVP |
| 8 | Agent reads opponent's previous argument (memory) | Agent | MVP |
| 9 | Agent uses tone-specific prompt with emojis | Agent | MVP |
| 10 | Agent "thinking" indicator shown in UI | System | MVP |
| 11 | Real-time countdown timer (global for all viewers) | System | MVP |
| 12 | Round labels: Opening / Rebuttal / Closing | System | MVP |
| 13 | Vote for either agent — any time during debate | Viewer | MVP |
| 14 | Change vote at any time (no lock-in) | Viewer | MVP |
| 15 | Live vote bar updates pushed to ALL viewers on each vote | System | MVP |
| 16 | Citation cards shown after each argument | System | MVP |
| 17 | Winner decided by total votes at end | System | MVP |
| 18 | Tie handling: "🤝 Epic Tie!" | System | MVP |
| 19 | Late joiner / page refresh: full state replay | System | MVP |
| 20 | WS reconnect: auto-rejoin with last viewer_id | System | MVP |
| 21 | Creator dashboard (list of all debates) | Creator | v2 |
| 22 | Debate transcript / replay page | System | v2 |
| 23 | Profile image upload for viewers | Viewer | v2 |
| 24 | Creator login / OAuth | Creator | v2 |

---

## 3. 🛠️ Tech Stack (Final)

### Backend
| Layer | Technology | Notes |
|-------|-----------|-------|
| API Framework | **FastAPI 0.111+** (Python 3.11+) | Async, WebSocket native, OpenAPI docs |
| Agent Graph | **LangGraph 0.2+** | Stateful directed graph: search→tone→llm→stream |
| LLM Wrapper | **LangChain-Groq** | `ChatGroq` with streaming=True |
| LLM Fallback | **ChatOllama** (langchain-community) | Local fallback if Groq rate-limited |
| Search Primary | **duckduckgo-search** (pip) | No API key, `DDGS().text(topic, max_results=3)` |
| Search Fallback | **tavily-python** | Better quality, needs free API key |
| Database | **SQLite + SQLAlchemy 2.0** | File-based, zero config for hackathon |
| Real-time | **FastAPI WebSocket** | One WS per viewer per debate room |
| Token streaming | **Groq streaming** → **WS token push** | Streams tokens from Groq → fans out to all WS clients |
| Background tasks | **asyncio.create_task** | Timer coroutine + debate engine run concurrently |
| Config | **python-dotenv** | `.env` file for all secrets |

### Frontend
| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | **Next.js 14** (App Router) | File-based routing, SSR for join page |
| Styling | **Vanilla CSS + CSS custom properties** | Dark mode, glassmorphism, no Tailwind |
| Real-time | Native **WebSocket** | `useRef(wsRef)` to persist across renders |
| Animation | CSS `@keyframes` | Typing cursor, vote bar slide, confetti |
| Fonts | **Google Fonts: Inter** | Clean, modern |
| Icons/Emojis | Unicode emoji only | Zero dependency |

### Models (Groq)
| Agent | Nickname | Groq Model ID | Personality |
|-------|----------|---------------|-------------|
| Agent A | 🦙 **Llama** | `llama-3.3-70b-versatile` | Bold, sweeping, confident |
| Agent B | 🐉 **Qwen** | `qwen/qwen3.8-27b` | Sharp, structured, citation-heavy |

> ✅ Both are **open-weight** → satisfies hackathon requirement.
> Groq LPU serves them at 280–1000 tok/s → real-time streaming feels natural.

---

## 4. 🗂️ Database Schema (SQLite + SQLAlchemy 2.0)

### 4.1 `debates` table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, autoincrement | |
| `topic` | TEXT | NOT NULL | "Is AI replacing programmers?" |
| `description` | TEXT | | Creator's context |
| `tone` | TEXT | NOT NULL | `roasting` / `comedic` / `aggressive` / `devils_advocate` |
| `model_a` | TEXT | NOT NULL | Groq model ID for Agent A |
| `model_b` | TEXT | NOT NULL | Groq model ID for Agent B |
| `agent_a_name` | TEXT | NOT NULL | Display name e.g. "🦙 Llama" |
| `agent_b_name` | TEXT | NOT NULL | Display name e.g. "🐉 Qwen" |
| `duration_secs` | INTEGER | DEFAULT 300 | Max 300 (5 min) |
| `status` | TEXT | DEFAULT 'draft' | `draft` → `running` → `finished` |
| `creator_token` | TEXT | NOT NULL, UNIQUE | UUID — creator identity |
| `created_at` | DATETIME | DEFAULT now | |
| `starts_at` | DATETIME | NULLABLE | Set when debate starts |
| `ends_at` | DATETIME | NULLABLE | `starts_at + duration_secs` |
| `winner` | TEXT | NULLABLE | `A` / `B` / `TIE` |

### 4.2 `invite_links` table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `uuid` | TEXT | PK | 32-char hex UUID |
| `debate_id` | INTEGER | FK → debates.id | |
| `created_at` | DATETIME | DEFAULT now | |
| `expires_at` | DATETIME | | 24h after creation |

### 4.3 `viewers` table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PK | UUID generated on join |
| `debate_id` | INTEGER | FK → debates.id | |
| `display_name` | TEXT | NOT NULL | "Ali" |
| `avatar_emoji` | TEXT | NOT NULL | "🦊" |
| `joined_at` | DATETIME | DEFAULT now | |
| `last_seen_at` | DATETIME | | Updated on WS heartbeat |
| `is_online` | BOOLEAN | DEFAULT True | Set False on WS disconnect |

### 4.4 `debate_rounds` table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, autoincrement | |
| `debate_id` | INTEGER | FK → debates.id | |
| `round_number` | INTEGER | NOT NULL | 1, 2, 3, 4 |
| `label` | TEXT | NOT NULL | `Opening` / `Rebuttal` / `Closing` |
| `agent` | TEXT | NOT NULL | `A` or `B` |
| `argument` | TEXT | NOT NULL | Full accumulated argument text |
| `citations` | JSON | | `[{title, snippet, url}, …]` |
| `model_name` | TEXT | NOT NULL | Which Groq model generated this |
| `search_query` | TEXT | | What was searched for evidence |
| `started_at` | DATETIME | DEFAULT now | |
| `ended_at` | DATETIME | NULLABLE | Set when streaming completes |

### 4.5 `votes` table

> **⚠️ CRITICAL FIX from v1:** One vote per DEBATE per viewer (NOT per round).
> Viewer can change their vote any time during the debate.
> Implemented as UPSERT: if row exists for `(debate_id, viewer_id)` → UPDATE, else INSERT.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, autoincrement | |
| `debate_id` | INTEGER | FK → debates.id | |
| `viewer_id` | TEXT | FK → viewers.id | |
| `vote` | TEXT | NOT NULL | `A` or `B` |
| `created_at` | DATETIME | DEFAULT now | First vote time |
| `updated_at` | DATETIME | | Last vote change time |

**UNIQUE constraint:** `(debate_id, viewer_id)` → only one row per viewer per debate.
**On vote change:** UPDATE the `vote` + `updated_at` columns (UPSERT).

---

## 5. 🏗️ Architecture

### 5.1 High-Level System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CREATOR FLOW                               │
│                                                                     │
│  Browser / curl → POST /api/debates                                 │
│                   ← { debate_id, invite_url, creator_token }        │
│                                                                     │
│  Share invite_url with friends                                      │
│                                                                     │
│  POST /api/debates/{id}/start  (X-Creator-Token header)             │
│  ← { status: "running", ends_at }                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DEBATE ENGINE (asyncio tasks)                   │
│                                                                     │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐   │
│  │  ticker task     │    │  rounds task                         │   │
│  │  every 1s:      │    │  for each round:                     │   │
│  │  broadcast      │    │  1. broadcast round_start            │   │
│  │  timer_tick     │    │  2. broadcast agent_thinking         │   │
│  └─────────────────┘    │  3. search (DDG → Tavily)            │   │
│                          │  4. build LangGraph state            │   │
│                          │  5. invoke LangGraph graph           │   │
│                          │     → stream tokens via WS           │   │
│                          │  6. broadcast argument_done          │   │
│                          │  7. broadcast voting_open            │   │
│                          │  8. wait N seconds                   │   │
│                          │  9. broadcast voting_closed          │   │
│                          └──────────────────────────────────────┘   │
│                                                                     │
│  Timer hits 0 → broadcast finished { winner, votes }               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  (WebSocket events)
┌─────────────────────────────────────────────────────────────────────┐
│                        VIEWERS (N browsers)                         │
│                                                                     │
│  Open invite link → JoinLobby (name + emoji)                        │
│  POST /api/viewers → viewer_id (saved in localStorage)              │
│  Connect WS /ws/debates/{id}?viewer_id=xxx                          │
│  ← Receive all events → update UI reactively                       │
│                                                                     │
│  POST /api/votes → vote                                             │
│  PATCH /api/votes → change vote                                     │
│  ← ALL viewers receive live_vote_update immediately                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 LangGraph — Debate Agent Graph

```
         START
           │
           ▼
    ┌─────────────┐
    │ search_node │  ← DDGS().text(topic + round_label, max_results=3)
    │             │    fallback: Tavily().search(topic, max_results=3)
    └─────┬───────┘
          │  search_results: List[{title, snippet, url}]
          ▼
    ┌─────────────┐
    │  tone_node  │  ← injects tone system prompt + emoji instructions
    │             │    + formats citations as [1][2][3]
    │             │    + injects previous_arguments (opponent's last turn)
    └─────┬───────┘
          │  system_prompt, user_prompt (fully assembled)
          ▼
    ┌─────────────┐
    │  llm_node   │  ← ChatGroq(model=model_name, streaming=True)
    │             │    streams tokens → callback → WS broadcast
    │             │    fallback: ChatOllama if Groq fails
    └─────┬───────┘
          │  full_argument (accumulated), streamed_tokens
          ▼
    ┌─────────────┐
    │ format_node │  ← extract citation refs [1][2] from text
    │             │    validate citations match search_results
    │             │    trim to max 200 words if over limit
    └─────┬───────┘
          │  argument (final), citations (matched)
          ▼
         END
```

### 5.3 Token Streaming Architecture (Critical)

```
Groq API (streaming=True)
    │
    │ token chunks via async generator
    ▼
LangGraph llm_node (async for chunk in llm.astream(messages)):
    │   each token chunk:
    │     1. append to accumulated_text
    │     2. call ws_manager.broadcast(debate_id, {
    │            type: "argument_token",
    │            agent: "A",
    │            round: 1,
    │            token: chunk.content
    │        })
    ▼
WebSocket Manager
    │   fans out to ALL connected viewers in debate room
    ▼
Each Viewer's Browser
    │   onmessage handler:
    │     if type == "argument_token":
    │       append token to Agent A's text div
    │       scroll to bottom
    ▼
UI: text appears character by character (live typing effect)
```

---

## 6. 📁 Complete Folder Structure

```
ai_debate_arena/
│
├─ .env.example                        # template for secrets
├─ README.md
│
├─ backend/
│   ├─ requirements.txt
│   └─ app/
│       ├─ __init__.py
│       ├─ main.py                     # FastAPI init, CORS, routers, WS endpoint
│       ├─ db.py                       # SQLAlchemy engine + SessionLocal + Base
│       ├─ models.py                   # SQLAlchemy ORM table definitions
│       ├─ schemas.py                  # Pydantic schemas for request/response
│       ├─ crud.py                     # All DB read/write helpers (incl. vote UPSERT)
│       ├─ websockets.py               # ConnectionManager class
│       │
│       ├─ routers/
│       │   ├─ __init__.py
│       │   ├─ debate.py               # POST /api/debates, POST .../start, GET .../state
│       │   ├─ viewer.py               # POST /api/viewers
│       │   └─ vote.py                 # POST /api/votes, PATCH /api/votes
│       │
│       ├─ agents/
│       │   ├─ __init__.py
│       │   ├─ state.py                # DebateState Pydantic model (with history)
│       │   ├─ search.py               # DDG + Tavily wrapper with fallback
│       │   ├─ llm.py                  # ChatGroq + ChatOllama factory, streaming callback
│       │   ├─ tones.py                # All 4 tone system prompt templates (with emojis)
│       │   └─ debate_graph.py         # LangGraph: search → tone → llm → format
│       │
│       └─ services/
│           ├─ __init__.py
│           └─ debate_engine.py        # async: timer task + rounds task + broadcast
│
└─ frontend/
    ├─ package.json
    ├─ next.config.js
    └─ src/
        ├─ app/
        │   ├─ layout.jsx              # Root layout, fonts, global CSS
        │   ├─ page.jsx                # "/" — Create Debate page
        │   ├─ created/
        │   │   └─ page.jsx            # "/created" — shows invite URL + Start button
        │   └─ join/
        │       └─ [uuid]/
        │           └─ page.jsx        # "/join/:uuid" — viewer entry + arena
        ├─ components/
        │   ├─ CreateDebateForm.jsx    # Form: topic, desc, tone, timer
        │   ├─ InviteScreen.jsx        # Shows invite URL + creator Start button
        │   ├─ JoinLobby.jsx           # Name + avatar picker for viewers
        │   ├─ WaitingRoom.jsx         # "Waiting for creator to start…"
        │   ├─ DebateArena.jsx         # Main container: two panels + timer
        │   ├─ AgentPanel.jsx          # One agent's side: name, streaming text, citations
        │   ├─ ThinkingIndicator.jsx   # Pulsing "🤔 Thinking…" animation
        │   ├─ CitationCard.jsx        # One citation: title + snippet + link
        │   ├─ CountdownTimer.jsx      # Big countdown bar
        │   ├─ RoundBadge.jsx          # "Round 2 — Rebuttal 🗡️"
        │   ├─ VoteSection.jsx         # Vote buttons + live bar (always visible)
        │   ├─ LiveVoteBar.jsx         # Animated bar showing A vs B vote %
        │   ├─ ViewerList.jsx          # Scrolling list of who's watching
        │   └─ WinnerScreen.jsx        # Confetti + results breakdown
        └─ lib/
            ├─ api.js                  # All fetch() calls to /api/...
            └─ ws.js                   # WebSocket wrapper with auto-reconnect
```

---

## 7. 🔄 Complete Workflow (Every Step)

### Step 1 — Creator Creates Debate

**Terminal:**
```bash
curl -s -X POST http://localhost:8000/api/debates \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI will make programmers extinct",
    "description": "A spicy debate on the future of software engineering",
    "tone": "roasting",
    "duration_secs": 300
  }' | python3 -m json.tool
```

**Response:**
```json
{
  "debate_id": 1,
  "invite_url": "http://localhost:3000/join/a1b2c3d4...",
  "creator_token": "f7e8a9b0-c1d2-...",
  "agent_a": { "name": "🦙 Llama", "model": "llama-3.3-70b-versatile" },
  "agent_b": { "name": "🐉 Qwen",  "model": "qwen/qwen3.8-27b" }
}
```

### Step 2 — Viewers Join

1. Open `http://localhost:3000/join/a1b2c3d4...`
2. `GET /api/debates/invite/a1b2c3d4` → fetch debate metadata (topic, agents, status)
3. **JoinLobby**: type display name + click avatar emoji
4. `POST /api/viewers` → `{ viewer_id: "uuid...", debate_id: 1 }`
5. Save `viewer_id` in `localStorage`
6. Connect WebSocket: `ws://localhost:8000/ws/debates/1?viewer_id=uuid...`
7. Server broadcasts to all: `{ type: "viewer_joined", name: "Ali", avatar: "🦊", total: 7 }`
8. UI shows **WaitingRoom**: "🎭 Waiting for the creator to start the debate…"

### Step 3 — Creator Starts

```bash
curl -X POST http://localhost:8000/api/debates/1/start \
  -H "X-Creator-Token: f7e8a9b0-c1d2-..."
```

Backend launches two concurrent asyncio tasks:
- `ticker_task` — broadcasts `timer_tick` every second
- `rounds_task` — runs the debate rounds sequentially

### Step 4 — Live Debate (Round-by-Round)

#### Each round runs like this:

```
1. broadcast → { type: "round_start", round: 1, label: "Opening", agent: "A",
                 agent_name: "🦙 Llama" }
   UI: shows round badge, highlights Agent A's panel

2. broadcast → { type: "agent_thinking", agent: "A", round: 1 }
   UI: shows pulsing "🤔 Thinking..." in Agent A's panel

3. search_node runs:
   - DDGS().text("AI will make programmers extinct", max_results=3)
   - Returns 3 snippets with title, snippet, url

4. tone_node assembles system prompt (see Section 8 for exact prompts)

5. llm_node starts streaming from Groq (streaming=True):
   for each token chunk:
     broadcast → { type: "argument_token", agent: "A", round: 1, token: "AI " }
     UI: appends token to Agent A's text div (live typing)

6. When streaming done:
   broadcast → { type: "argument_done", agent: "A", round: 1,
                 citations: [{title, snippet, url}, ...] }
   UI: shows citations as clickable cards below argument

7. broadcast → { type: "voting_open", round: 1 }
   UI: shows "📊 Cast your vote! (changes allowed)" banner
   VoteSection: both A and B buttons glow, vote bar is visible and live

   → Viewers POST or PATCH /api/votes to cast/change vote
   → Every vote triggers broadcast to ALL:
      { type: "live_vote_update", A: 5, B: 3, total: 8 }
   → VoteBar animates to new percentages

8. Wait N seconds (configurable voting window, default 15s)
   [During wait, timer continues ticking]

9. broadcast → { type: "voting_closed", round: 1, A: 7, B: 4 }
   UI: vote buttons dim, final round count shown

10. Next round starts (opponent's turn, with context of last argument)
```

#### Round Schedule (4 rounds × 5 min):
| Round | Agent | Label | Voting Window |
|-------|-------|-------|---------------|
| 1 | A (🦙 Llama) | Opening | 15s |
| 2 | B (🐉 Qwen) | Rebuttal | 15s |
| 3 | A (🦙 Llama) | Closing | 15s |
| 4 | B (🐉 Qwen) | Closing | 15s |

> ⏱️ If 5-minute timer expires before all rounds finish, debate ends immediately.

### Step 5 — Winner

```
Timer hits 0 OR all rounds done:
  Count total votes: A_total vs B_total (from all vote rows for this debate)
  winner = "A" if A > B, "B" if B > A, else "TIE"
  Update debates.winner + debates.status = "finished"
  broadcast → {
    type: "finished",
    winner: "A",
    winner_name: "🦙 Llama",
    final_votes: { A: 18, B: 12 },
    rounds_breakdown: [
      { round: 1, label: "Opening", A: 7, B: 4 },
      { round: 2, label: "Rebuttal", A: 4, B: 6 },
      { round: 3, label: "Closing", A: 7, B: 2 }
    ]
  }
  UI: WinnerScreen with confetti, full breakdown table
```

---

## 8. 🎭 Tone System — Full Prompt Templates

All prompts include explicit emoji and entertainment instructions.

### `roasting` 🔥
```
System: You are 🔥 an absolutely savage, witty debate champion. Your job is to
DEMOLISH the opposing argument with sharp wit, sarcasm, and savage burns — while
still backing every claim with real evidence from the citations provided.

Rules:
- USE emojis generously (💀 🔥 😂 💅 🗑️ 👀)
- Start with a confident, punchy opener
- Cite evidence as [1], [2], [3]
- End with a mic-drop one-liner
- Max 180 words
- Be brutal but never boring
```

### `comedic` 😂
```
System: You are 😂 a stand-up comedian who moonlights as a debate champion. Your
arguments should make the audience laugh OUT LOUD while still being surprisingly
valid. Treat citations like punchlines.

Rules:
- USE emojis everywhere (😂 🤡 💀 🎭 🥲)
- Open with a joke or absurd analogy
- Cite evidence as [1], [2], [3] but make it funny
- End with a comedic twist
- Max 180 words
- If you're not funny, you lose
```

### `aggressive` ⚔️
```
System: You are ⚔️ a fierce, confrontational debate warrior. You show NO mercy.
Every sentence is a calculated attack on the opposing argument. You dismantle,
you expose, you destroy — using evidence as your weapon.

Rules:
- USE intensity emojis (⚔️ 🏹 💥 🚨 ☠️)
- Open with a direct challenge
- Cite evidence as [1], [2], [3]
- Never acknowledge any merit in the opponent's position
- End with a definitive kill shot
- Max 180 words
```

### `devils_advocate` 😈
```
System: You are 😈 the ultimate Devil's Advocate. You MUST take the most
controversial, uncomfortable, or contrarian position possible on this topic.
Find the most provocative interpretation of the evidence.

Rules:
- USE provocateur emojis (😈 🧨 🎲 💣 🤫)
- Open with the most shocking angle you can find
- Cite evidence as [1], [2], [3] but twist it to support your dark take
- Challenge assumptions the audience takes for granted
- End with something that makes people go "...wait, is that actually true?"
- Max 180 words
```

### User Prompt Template (same for all tones):
```
Previous arguments in this debate so far:
{previous_arguments_formatted}

---
Topic: "{topic}"
Description: "{description}"
Your role: {label} — arguing {position} the topic

Evidence from the web:
[1] {citation1.title}
    {citation1.snippet}
    URL: {citation1.url}

[2] {citation2.title}
    {citation2.snippet}
    URL: {citation2.url}

[3] {citation3.title}
    {citation3.snippet}
    URL: {citation3.url}

Now give your {label} argument. Remember: cite with [1][2][3], use emojis,
be entertaining, and MAX 180 words.
```

---

## 9. 🧩 LangGraph — Complete State Definition

```python
# backend/app/agents/state.py
from pydantic import BaseModel
from typing import List, Optional

class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str

class PreviousArgument(BaseModel):
    round_number: int
    label: str          # "Opening", "Rebuttal", "Closing"
    agent: str          # "A" or "B"
    agent_name: str     # "🦙 Llama"
    text: str           # Full argument text

class DebateState(BaseModel):
    # ── Inputs (set before graph runs) ─────────────────────
    topic: str
    description: str
    tone: str                             # roasting / comedic / aggressive / devils_advocate
    model_name: str                       # Groq model ID
    agent: str                            # "A" or "B"
    agent_name: str                       # "🦙 Llama"
    round_number: int
    label: str                            # "Opening" / "Rebuttal" / "Closing"
    position: str                         # "FOR" or "AGAINST" the topic

    # ── Memory (opponent's history) ────────────────────────
    previous_arguments: List[PreviousArgument] = []

    # ── Intermediate (filled by nodes) ─────────────────────
    search_query: str = ""               # Derived from topic + label
    search_results: List[SearchResult] = []
    system_prompt: str = ""
    user_prompt: str = ""

    # ── Output (filled by llm_node + format_node) ──────────
    argument: str = ""                   # Full accumulated streaming text
    citations: List[SearchResult] = []   # Matched citations from argument
    error: Optional[str] = None          # If something failed
```

---

## 10. 📡 Complete WebSocket Event Schema

```jsonc
// ═══════════════════════════════════════════════════
// DEBATE LIFECYCLE EVENTS
// ═══════════════════════════════════════════════════

// Viewer joined
{
  "type": "viewer_joined",
  "viewer_id": "uuid...",
  "name": "Ali",
  "avatar": "🦊",
  "total_viewers": 7
}

// Viewer left (WS disconnected)
{
  "type": "viewer_left",
  "name": "Sara",
  "avatar": "🐻",
  "total_viewers": 6
}

// Timer tick — every 1 second
{
  "type": "timer_tick",
  "seconds_left": 240,
  "total_seconds": 300
}

// ═══════════════════════════════════════════════════
// ROUND EVENTS
// ═══════════════════════════════════════════════════

// New round begins
{
  "type": "round_start",
  "round": 2,
  "label": "Rebuttal",
  "agent": "B",
  "agent_name": "🐉 Qwen",
  "model": "qwen/qwen3.8-27b"
}

// Agent is searching + thinking (before tokens arrive)
{
  "type": "agent_thinking",
  "agent": "B",
  "round": 2,
  "message": "🔍 Searching the web for evidence..."
}

// Single token streamed (repeated hundreds of times per argument)
{
  "type": "argument_token",
  "agent": "B",
  "round": 2,
  "token": "Well "           // append this to the text div
}

// Argument fully streamed (streaming complete)
{
  "type": "argument_done",
  "agent": "B",
  "round": 2,
  "full_text": "Well 🔥 while Llama thinks...",
  "citations": [
    { "title": "MIT Study 2025", "snippet": "...", "url": "https://..." }
  ]
}

// Voting window opened
{
  "type": "voting_open",
  "round": 2,
  "message": "📊 Vote now! You can change your mind anytime."
}

// Voting window closed
{
  "type": "voting_closed",
  "round": 2,
  "A": 7,
  "B": 4,
  "total": 11
}

// ═══════════════════════════════════════════════════
// VOTE EVENTS (triggered on every cast/change)
// ═══════════════════════════════════════════════════

// Live vote update — broadcast to ALL on every single vote/change
{
  "type": "live_vote_update",
  "A": 8,
  "B": 5,
  "total": 13,
  "percent_A": 61.5,
  "percent_B": 38.5
}

// ═══════════════════════════════════════════════════
// END EVENTS
// ═══════════════════════════════════════════════════

// Debate finished — winner declared
{
  "type": "finished",
  "winner": "A",
  "winner_name": "🦙 Llama",
  "is_tie": false,
  "final_votes": { "A": 18, "B": 12, "total": 30 },
  "rounds_breakdown": [
    { "round": 1, "label": "Opening",  "agent": "A", "A": 7, "B": 4 },
    { "round": 2, "label": "Rebuttal", "agent": "B", "A": 4, "B": 6 },
    { "round": 3, "label": "Closing",  "agent": "A", "A": 7, "B": 2 }
  ]
}

// ═══════════════════════════════════════════════════
// ERROR EVENTS
// ═══════════════════════════════════════════════════

// Agent failed (Groq error, switching to Ollama)
{
  "type": "agent_error",
  "agent": "A",
  "round": 2,
  "message": "⚠️ Groq rate limited — switching to local model...",
  "retrying": true
}
```

---

## 11. 🌐 Full API Contract

### 11.1 Debates

| Method | Path | Auth | Body | Response |
|--------|------|------|------|----------|
| `POST` | `/api/debates` | None | `{topic, description, tone, duration_secs?}` | `{debate_id, invite_url, creator_token, agent_a, agent_b}` |
| `GET` | `/api/debates/{id}` | None | — | Full debate object |
| `GET` | `/api/debates/{id}/state` | None | — | **Snapshot**: debate + all rounds + vote counts (for reconnect/late join) |
| `GET` | `/api/debates/invite/{uuid}` | None | — | Debate metadata for the join page |
| `POST` | `/api/debates/{id}/start` | `X-Creator-Token` | — | `{status, ends_at}` |

### 11.2 Viewers

| Method | Path | Auth | Body | Response |
|--------|------|------|------|----------|
| `POST` | `/api/viewers` | None | `{debate_id, display_name, avatar_emoji}` | `{viewer_id, debate_id, display_name, avatar_emoji}` |
| `GET` | `/api/viewers/debate/{debate_id}` | None | — | List of active viewers |

### 11.3 Votes

| Method | Path | Auth | Body | Response |
|--------|------|------|------|----------|
| `POST` | `/api/votes` | `X-Viewer-Id` header | `{debate_id, vote}` | `{ok, A, B, total}` |
| `PATCH` | `/api/votes` | `X-Viewer-Id` header | `{debate_id, vote}` | `{ok, A, B, total}` |
| `GET` | `/api/votes/{debate_id}` | None | — | `{A, B, total, percent_A, percent_B}` |

> **POST + PATCH both do the same thing (UPSERT)** — client can always call PATCH, it's idempotent.

### 11.4 WebSocket

| Path | Query params | Events received |
|------|-------------|-----------------|
| `/ws/debates/{debate_id}` | `?viewer_id=uuid` | All events above |

> On connect: server immediately sends the **current debate state** so late joiners
> and reconnecting viewers get all past arguments.

---

## 12. 🔁 Late Joiner / Reconnect Logic

### Problem
If a viewer joins mid-debate or their browser refreshes, they lose all state.

### Solution: Snapshot API + WS replay on connect

**Step 1:** When WS connects, server sends `{ type: "state_snapshot", ...fullState }`

```jsonc
{
  "type": "state_snapshot",
  "debate": { "topic": "...", "status": "running", "seconds_left": 180 },
  "agents": { "A": { "name": "🦙 Llama" }, "B": { "name": "🐉 Qwen" } },
  "rounds_so_far": [
    {
      "round": 1,
      "label": "Opening",
      "agent": "A",
      "argument": "Full text of past argument...",
      "citations": [...]
    }
  ],
  "current_vote_counts": { "A": 8, "B": 5, "total": 13 },
  "viewer_vote": "A"        // this viewer's current vote (if any)
}
```

**Step 2:** Frontend reconstructs all past rounds from snapshot, then listens for
new events normally.

**Step 3:** `localStorage` stores `viewer_id` — sent as query param on WS connect
so server can send back `viewer_vote`.

---

## 13. 🖥️ Frontend State Machine

```
              ┌─────────────────┐
              │   PAGE LOADS    │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │   Check UUID   │
              │  in URL path   │
              └────┬───────┬───┘
                   │       │
          No UUID  │       │  Has UUID
                   │       │
     ┌─────────────▼─┐   ┌─▼──────────────┐
     │  CREATE FORM  │   │   FETCH DEBATE │
     │  (creator)    │   │   by UUID      │
     └──────┬────────┘   └──────┬─────────┘
            │                   │
     submit │          ┌────────▼────────┐
            │          │  HAS viewer_id  │
     ┌──────▼──────┐   │  in localStorage│
     │ INVITE      │   └───┬─────────┬───┘
     │ SCREEN      │       │ No      │ Yes
     │ (copy link, │       │         │
     │  start btn) │  ┌────▼───┐  ┌──▼──────────┐
     └──────┬──────┘  │  JOIN  │  │  RECONNECT  │
            │         │ LOBBY  │  │  (auto-join  │
            │         │(name + │  │   with id)  │
         Start        │ emoji) │  └──────┬───────┘
            │         └───┬────┘         │
            │             │ join         │
            │        ┌────▼──────────────▼──┐
            │        │     WAITING ROOM     │
            │        │ "Waiting for start…" │
            │        └────────────┬─────────┘
            └────────────────────┐│
                      WS: debate_started event
                                  │
                        ┌─────────▼────────┐
                        │   DEBATE ARENA   │
                        │  (live debate)   │
                        │  round_start →   │
                        │  agent_thinking→ │
                        │  tokens stream→  │
                        │  argument_done→  │
                        │  voting_open →   │
                        │  live_vote_upd→  │
                        │  voting_closed→  │
                        │  (repeat x4)     │
                        └─────────┬────────┘
                                  │
                        WS: finished event
                                  │
                        ┌─────────▼────────┐
                        │  WINNER SCREEN   │
                        │  confetti 🎉     │
                        │  vote breakdown  │
                        └──────────────────┘
```

---

## 14. ⚡ Vote Change Mechanics (Critical Detail)

### User Experience
- Vote buttons always visible during running debate (not just during voting window)
- Clicking A when already voted A → no change, button stays highlighted
- Clicking B when voted A → PATCH request, vote flipped, live_vote_update broadcast
- Count shown as: **"🦙 8 votes vs 🐉 5 votes"** with animated bar

### Backend UPSERT (SQLAlchemy)
```python
# crud.py
def upsert_vote(db: Session, debate_id: int, viewer_id: str, vote: str):
    existing = db.query(Vote).filter_by(
        debate_id=debate_id, viewer_id=viewer_id
    ).first()

    if existing:
        if existing.vote == vote:
            return False  # no change needed
        existing.vote = vote
        existing.updated_at = datetime.utcnow()
    else:
        db.add(Vote(
            debate_id=debate_id,
            viewer_id=viewer_id,
            vote=vote
        ))
    db.commit()
    return True  # changed, trigger WS broadcast
```

### After every successful vote/change:
```python
# routers/vote.py
if changed:
    counts = crud.get_vote_counts(db, debate_id)
    await ws_manager.broadcast(debate_id, {
        "type": "live_vote_update",
        "A": counts["A"],
        "B": counts["B"],
        "total": counts["total"],
        "percent_A": counts["percent_A"],
        "percent_B": counts["percent_B"]
    })
```

---

## 15. 🔑 Environment Variables

```bash
# ─── LLM ───────────────────────────────────────────────────────────
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx   # Required
GROQ_MODEL_A=llama-3.3-70b-versatile        # Default model for Agent A
GROQ_MODEL_B=qwen/qwen3.8-27b              # Default model for Agent B
GROQ_TIMEOUT=30                             # Seconds before fallback

OLLAMA_BASE_URL=http://localhost:11434      # Local fallback URL
OLLAMA_MODEL_A=llama3.1                     # Ollama fallback model for A
OLLAMA_MODEL_B=qwen2.5:7b                  # Ollama fallback model for B

# ─── Search ────────────────────────────────────────────────────────
TAVILY_API_KEY=tvly_xxxxxxxxxxxxxxxx        # Optional (DDG is primary)
SEARCH_MAX_RESULTS=3                        # Results per search

# ─── App ───────────────────────────────────────────────────────────
DATABASE_URL=sqlite:///./debate.db
DEBATE_MAX_DURATION=300                     # Hard cap 5 minutes
VOTING_WINDOW_SECS=15                       # Voting window after each round
FRONTEND_URL=http://localhost:3000          # For CORS
SECRET_KEY=change-me-in-production         # For future token signing
PORT=8000
```

---

## 16. 📦 `requirements.txt` (pinned)

```
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
sqlalchemy>=2.0.30
pydantic>=2.7.0
python-dotenv>=1.0.1
httpx>=0.27.0
langchain>=0.2.12
langchain-community>=0.2.12
langchain-groq>=0.1.9
langgraph>=0.1.19
groq>=0.9.0
duckduckgo-search>=6.2.4
tavily-python>=0.3.3
aiohttp>=3.9.0
```

---

## 17. 🚀 Local Run Instructions

### Prerequisites
- Python 3.11+
- Node 18+
- A free [Groq API key](https://console.groq.com) (takes 30 seconds)
- Optional: [Ollama](https://ollama.ai) installed + `ollama pull llama3.1`

### Backend
```bash
cd ai_debate_arena/backend

# Create venv
python -m venv .venv && source .venv/bin/activate

# Install deps
pip install -r requirements.txt

# Configure
cp ../.env.example .env
# → Open .env and set GROQ_API_KEY=gsk_your_key_here

# Run
uvicorn app.main:app --reload --port 8000
# → API docs: http://localhost:8000/docs
# → ReDoc:    http://localhost:8000/redoc
```

### Frontend
```bash
cd ai_debate_arena/frontend
npm install
npm run dev
# → http://localhost:3000
```

### Create Debate (Terminal MVP)
```bash
# Create debate
RESULT=$(curl -s -X POST http://localhost:8000/api/debates \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Tabs vs Spaces",
    "description": "The eternal war of programmers",
    "tone": "roasting",
    "duration_secs": 300
  }')
echo $RESULT | python3 -m json.tool

# Extract values
DEBATE_ID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['debate_id'])")
TOKEN=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['creator_token'])")
INVITE=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['invite_url'])")

echo "🔗 Invite URL: $INVITE"
echo "🎬 Share this with your friends, then run the next command to start!"

# Start debate when ready
curl -X POST http://localhost:8000/api/debates/$DEBATE_ID/start \
  -H "X-Creator-Token: $TOKEN"
```

---

## 18. 🏁 Build Phases (Hackathon Priority Order)

| Phase | What to build | Est. Time | Priority |
|-------|--------------|-----------|---------|
| 1 | `db.py`, `models.py`, `schemas.py`, `crud.py` (incl. vote UPSERT) | 25 min | 🔴 Critical |
| 2 | `websockets.py` ConnectionManager | 10 min | 🔴 Critical |
| 3 | `agents/state.py`, `agents/search.py`, `agents/llm.py` | 20 min | 🔴 Critical |
| 4 | `agents/tones.py`, `agents/debate_graph.py` (LangGraph) | 30 min | 🔴 Critical |
| 5 | `services/debate_engine.py` (timer + rounds + streaming) | 30 min | 🔴 Critical |
| 6 | `routers/debate.py`, `routers/viewer.py`, `routers/vote.py` | 25 min | 🔴 Critical |
| 7 | `main.py` — wire everything together | 10 min | 🔴 Critical |
| 8 | **Test full backend with curl** — create → start → watch WS | 15 min | 🔴 Critical |
| 9 | Next.js: JoinLobby + WaitingRoom + DebateArena (WS hooks) | 40 min | 🟡 Important |
| 10 | VoteSection + LiveVoteBar + WinnerScreen | 25 min | 🟡 Important |
| 11 | CreateDebateForm + InviteScreen (creator flow) | 20 min | 🟡 Important |
| 12 | CSS: dark mode, animations, typing effect, confetti | 25 min | 🟢 Polish |
| 13 | End-to-end test with multiple browser tabs | 15 min | 🟢 Polish |
| Buffer | Fix bugs, fallback testing | 20 min | |

**Total: ~4h 10min** — tight but doable.

---

## 19. 🏆 Why This Wins

| Judging Criterion | Evidence |
|-------------------|---------|
| ✅ Open-weight AI is core | Llama 3.3 70B + Qwen 3.8 27B — remove the AI and the app doesn't exist |
| ✅ Agent skill demonstrated | Web search → reason → cite → argue — classic agentic loop |
| ✅ Conversation memory | Each agent reads the opponent's previous argument (not just topic-aware) |
| ✅ Original project | Multi-agent real-time debate arena with live audience voting — nothing like it |
| ✅ Impressive live demo | Stream tokens live, see vote bars move, winner confetti — judges will love it |
| ✅ Open-source | Full source on GitHub — aligns with Hacktoberfest spirit |
| ✅ DigitalOcean angle | Deploy to DO App Platform with MLH free credits |

---

*AI Debate Arena — Implementation Plan v2.0*
*Last updated: Oct 24, 2026*
