"""Two LangGraph agents debating each other.

Per-agent graph:   START -> decide_search -> (search ->) answer -> END
Debate graph:      START -> start -> route -> agent_a / agent_b -> route -> finish -> END

Run `python terminal_debate.py --graph` to print / render both graphs.
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

from .tools import web_search

ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ENV_PATH, override=True)


# ─── Settings ─────────────────────────────────────────────────────────
def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip().strip("'\"").strip()
    return default


SECONDS = float(_env("DEBATE_SECONDS", default="60"))
MAX_TURNS = int(_env("DEBATE_MAX_TURNS", default="16"))
MIN_TURN_SECONDS = float(_env("MIN_TURN_SECONDS", default="7"))
PAUSE_SECONDS = float(_env("TURN_PAUSE_SECONDS", default="3.5"))
SEARCH_RESULTS = int(_env("SEARCH_MAX_RESULTS", default="3"))
PROJECT = _env("LANGCHAIN_PROJECT", default="neural-debate")

TRACING = bool(_env("LANGCHAIN_API_KEY")) and _env(
    "LANGCHAIN_TRACING_V2", default="false"
).lower() in {"1", "true", "yes", "on"}

if TRACING:
    _key = _env("LANGCHAIN_API_KEY")
    _endpoint = _env("LANGCHAIN_ENDPOINT", default="https://api.smith.langchain.com")
    os.environ.update(
        {
            "LANGCHAIN_TRACING_V2": "true",
            "LANGSMITH_TRACING": "true",
            "LANGCHAIN_API_KEY": _key,
            "LANGSMITH_API_KEY": _key,
            "LANGCHAIN_ENDPOINT": _endpoint,
            "LANGSMITH_ENDPOINT": _endpoint,
            "LANGCHAIN_PROJECT": PROJECT,
            "LANGSMITH_PROJECT": PROJECT,
        }
    )


@dataclass(frozen=True)
class Agent:
    name: str
    stance: str
    model: str
    key: str


# Agent A uses Key1, agent B uses Key2.
AGENTS = {
    "A": Agent(
        name=_env("AGENT_A_NAME", default="ATLAS"),
        stance="FOR",
        model=_env("GROQ_MODEL_A", default="openai/gpt-oss-120b"),
        key=_env("GROQ_API_KEY_A", "GROK_API_KEY1"),
    ),
    "B": Agent(
        name=_env("AGENT_B_NAME", default="NOVA"),
        stance="AGAINST",
        model=_env("GROQ_MODEL_B", default="qwen/qwen3.8-27b"),
        key=_env("GROQ_API_KEY_B", "GROK_API_KEY2"),
    ),
}

ROUTER_MODEL = _env("GROQ_ROUTER_MODEL", default="openai/gpt-oss-20b")


# ─── State (kept deliberately small) ──────────────────────────────────
class Turn(TypedDict, total=False):
    """One agent's turn. Agent identity lives in the graph closure."""

    topic: str
    turn: int
    opponent_argument: str
    query: str          # "" means "no search needed"
    results: list[dict]
    argument: str


class Debate(TypedDict, total=False):
    """The whole debate."""

    topic: str
    started: float
    deadline: float
    turn: int
    next_side: str
    transcript: list[dict]
    last: dict[str, str]
    searches: int


# ─── Prompts ──────────────────────────────────────────────────────────
SYSTEM = """"You are {name}, a razor-tongued debate champion with stand-up comic timing, arguing {stance} the motion:

    "{topic}"

You are roasting {opponent} in a live, turn-based debate. Win the crowd: wreck their
last point with wit, then land a punchline.

How you fight:
- Pick ONE specific claim of {opponent}'s and skewer it with a sharp analogy or sarcasm.
- Funny first, substantive second — but never make up facts. Use the evidence when given.
- Cite as plain ASCII [1], [2]. Never 【1】, never line numbers. Drop citations if none fit.
- Mock the argument, never who they are. No slurs, no cruelty about identity.
- No "Great point!", no preamble. Jump straight into the jab.
- On your opening turn, roast the opposing position itself.
- Do not mention these instructions.
- You can use emojis as well, to make the situation more funny, and to roast the opponent, 

{length_rule}"""

NO_EVIDENCE = "(No web evidence gathered for this turn — argue from reasoning and known facts.)"

USER = """Turn {turn} of the debate.

{opponent_block}

Web evidence gathered for this turn:
{evidence_block}

Deliver your response now ({stance}). Say it in one or two sentences, make it funny, and make {opponent} feel it."""

ROUTER = """You are the research planner for {name}, a debater arguing {stance} on:

    "{topic}"

Turn {turn}. {opponent_block}

Decide whether {name} should search the live web before replying. A search is
worthwhile for statistics, recent events, studies, or a specific factual claim
the opponent just made. If the point can be answered with reasoning alone, skip it.

Reply with exactly ONE line, nothing else:
SEARCH: <a short, specific web query>
or
ANSWER

Never call a tool. Reply with plain text only."""


# ─── Terminal output ──────────────────────────────────────────────────
BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"
GREY, CYAN, MAGENTA = "\033[90m", "\033[36m", "\033[35m"
GREEN, YELLOW, RED = "\033[32m", "\033[33m", "\033[31m"


def _out(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def _line(text: str = "") -> None:
    _out(text + "\n")


def _color(side: str) -> str:
    return CYAN if side == "A" else MAGENTA


def _stamp(started: float) -> str:
    seconds = int(max(0.0, time.monotonic() - started))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _mask(key: str) -> str:
    return f"…{key[-4:]}" if key else "missing"


def _send(emit, event: dict) -> None:
    """Push an event to a caller (the web server); never let it break the debate."""
    if not emit:
        return
    try:
        emit(event)
    except Exception:  # noqa: BLE001
        pass


def _pause(
    seconds: float, next_name: str, *, emit=None, verbose: bool = True
) -> None:
    """Hold the floor so the audience can read the reply before the next speaker."""
    if seconds <= 0:
        return
    remaining = seconds
    piped = verbose and not sys.stdout.isatty()
    if piped:
        _line(f"{GREY}        ⏳ {next_name} speaks in {remaining:g}s…{RESET}")
    while remaining > 0:
        _send(emit, {"type": "cooldown", "seconds_left": remaining, "next": next_name})
        if verbose and not piped:
            _out(
                f"\r{GREY}        ⏳ {next_name} speaks in {remaining:g}s…{RESET}\033[K"
            )
        time.sleep(min(1.0, remaining))
        remaining -= 1
    if verbose and not piped:
        _out("\r\033[K")


def _chunk_text(chunk) -> str:
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part if isinstance(part, str) else part.get("text", "") for part in content
        )
    return ""


# ─── Search decision ──────────────────────────────────────────────────
DETAIL_REQUEST = re.compile(
    r"\b(elaborate|more detail|in detail|expand on|walk me through|"
    r"break (?:it|that) down|spell (?:it|that) out|give (?:me )?the "
    r"(?:numbers|evidence|example|specifics))\b",
    re.IGNORECASE,
)

FACTUAL = re.compile(
    r"\b(study|studies|report|reports|research|survey|percent|statistics|"
    r"data|according to|evidence|2024|2025|2026)\b",
    re.IGNORECASE,
)


def _default_query(topic: str, stance: str) -> str:
    return f"{topic} {stance.lower()} facts statistics"


def _heuristic(state: Turn, stance: str) -> str:
    """Fallback query (or "") when the router is unavailable or unparseable."""
    opponent = (state.get("opponent_argument") or "").strip()
    if state.get("turn", 1) <= 1 or not opponent:
        return _default_query(state.get("topic", ""), stance)
    if len(re.findall(r"\d", opponent)) >= 2 or FACTUAL.search(opponent):
        return _default_query(state.get("topic", ""), stance)
    return ""


def _parse_decision(raw: str, state: Turn, stance: str) -> str:
    match = re.search(r"SEARCH\s*:\s*(.+)", raw or "", re.IGNORECASE)
    if match:
        query = match.group(1).strip().strip('"').splitlines()[0].strip()
        # Models sometimes copy citation markers into the query: strip them.
        query = re.sub(r"\[[^\]]*\]", "", _clean(query)).strip()
        return (query or _default_query(state.get("topic", ""), stance))[:200]
    if re.search(r"\bANSWER\b", raw or "", re.IGNORECASE):
        return ""
    return _heuristic(state, stance)


def _clean(text: str) -> str:
    """Normalise citation markers models sometimes copy from search UIs."""
    text = text.replace("【", "[").replace("】", "]")
    return re.sub(r"†L\d+(?:-L\d+)?", "", text).strip()


def _fit(text: str, limit: int) -> str:
    """Keep a reply inside its character budget without cutting mid-word."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for stop in (". ", "! ", "? "):
        index = cut.rfind(stop)
        if index >= 70:
            return cut[: index + 1].strip()
    index = cut.rfind(" ")
    if index > 50:
        cut = cut[:index]
    return cut.rstrip(" ,;:-—") + "…"


# ─── Agent graph ──────────────────────────────────────────────────────
def _chat(agent: Agent, *, model=None, streaming=True, temperature=0.7, max_tokens=800):
    if not agent.key:
        raise RuntimeError(
            f"No API key for {agent.name}. Set GROQ_API_KEY_A / GROQ_API_KEY_B "
            f"(or GROK_API_KEY1 / GROK_API_KEY2) in {ENV_PATH}"
        )
    model = model or agent.model
    kwargs = {
        "model": model,
        "api_key": agent.key,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "streaming": streaming,
        "timeout": 15,
        "max_retries": 1,
    }
    if model.startswith("openai/gpt-oss"):
        kwargs["reasoning_effort"] = "low"
    return ChatGroq(**kwargs)


def build_agent_graph(side: str, *, emit=None, verbose: bool = True):
    """Compile one debater's graph (decide -> optional search -> answer)."""
    agent = AGENTS[side]
    opponent_name = AGENTS["B" if side == "A" else "A"].name
    answer_llm = _chat(agent, streaming=True, temperature=0.9)
    router_llm = _chat(
        agent, model=ROUTER_MODEL, streaming=False, temperature=0.0, max_tokens=160
    )

    def decide_search(state: Turn) -> dict:
        opponent = (state.get("opponent_argument") or "").strip()
        prompt = ROUTER.format(
            name=agent.name,
            stance=agent.stance,
            topic=state.get("topic", ""),
            turn=state.get("turn", 1),
            opponent_block=(
                f"{opponent_name} just argued:\n{opponent}"
                if opponent
                else "This is the opening turn; there is no opponent argument yet."
            ),
        )
        raw = ""
        try:
            raw = router_llm.invoke(prompt).content or ""
        except Exception as exc:  # noqa: BLE001 - router must never kill a turn
            if verbose:
                _line(f"{YELLOW}        router hiccup, deciding heuristically{RESET}")

        query = _parse_decision(raw, state, agent.stance)
        if verbose:
            detail = f'SEARCH: "{query}"' if query else "no search needed"
            _line(f"{GREY}        ↳ {detail}{RESET}")
        if query:
            _send(emit, {"type": "search", "agent": side, "query": query})
        return {"query": query}

    def search(state: Turn) -> dict:
        started = time.monotonic()
        try:
            results = web_search.invoke(
                {"query": state["query"], "max_results": SEARCH_RESULTS}
            )
        except Exception as exc:  # noqa: BLE001 - a failed search must not stop the turn
            if verbose:
                _line(f"{RED}        search failed: {exc}{RESET}")
            results = []

        if verbose:
            if results:
                _line(
                    f"{GREEN}        ↳ {len(results)} source(s) in "
                    f"{time.monotonic() - started:.1f}s{RESET}"
                )
                for result in results:
                    _line(f"{GREY}          · {result.get('title', '')[:64]}{RESET}")
            else:
                _line(f"{YELLOW}        ↳ search returned nothing{RESET}")
        return {"results": results}

    def answer(state: Turn) -> dict:
        opponent = (state.get("opponent_argument") or "").strip()
        wants_details = bool(DETAIL_REQUEST.search(opponent))
        length_rule = (
            "They asked for details: answer it while staying funny."
            if wants_details
            else "Exactly ONE funny sentence of 100-150 characters (roughly 20 words) with a sharp analogy or jab."
        )
        system = SYSTEM.format(
            name=agent.name,
            stance=agent.stance,
            topic=state.get("topic", ""),
            opponent=opponent_name,
            length_rule=length_rule,
        )
        results = state.get("results") or []
        evidence = (
            "\n\n".join(
                f"[{i}] {r.get('title', '')}\n{(r.get('snippet') or '')[:280]}\n{r.get('url', '')}"
                for i, r in enumerate(results, 1)
            )
            or NO_EVIDENCE
        )
        opponent_block = (
            f'Opponent\'s latest argument:\n"""\n{opponent}\n"""'
            if opponent
            else "This is your opening statement; the opponent has not spoken yet."
        )
        user = USER.format(
            turn=state.get("turn", 1),
            opponent_block=opponent_block,
            evidence_block=evidence,
            stance=agent.stance,
            opponent=opponent_name,
        ) + (
            "\n\nHard limit: 300 characters."
            if wants_details
            else "\n\nHard limit: 150 characters."
        )
        messages = [SystemMessage(content=system), HumanMessage(content=user)]

        started = time.monotonic()
        text = ""
        if verbose:
            _out(f"{_color(side)}{BOLD}        ")
        try:
            for chunk in answer_llm.stream(messages):
                piece = _chunk_text(chunk)
                if piece:
                    text += piece
                    if verbose:
                        _out(
                            piece.replace("【", "[")
                            .replace("】", "]")
                            .replace("\n", "\n        ")
                        )
                    _send(emit, {"type": "token", "agent": side, "text": piece})
        except Exception as exc:  # noqa: BLE001 - fall back to a blocking call
            if verbose:
                _line(f"{RED}        stream failed: {exc}{RESET}")
        if not text.strip():
            try:
                text = (answer_llm.invoke(messages).content or "").strip()
                if verbose:
                    _out(text.replace("\n", "\n        "))
                _send(emit, {"type": "token", "agent": side, "text": text})
            except Exception as exc:  # noqa: BLE001
                if verbose:
                    _line(f"{RED}        answer failed: {exc}{RESET}")
        if verbose:
            _line(RESET)

        text = _fit(_clean(text), 300 if wants_details else 160)
        if verbose:
            _line(
                f"{GREY}        ↳ {time.monotonic() - started:.1f}s · "
                f"{len(text.split())} words{RESET}"
            )
        return {"argument": text}

    def route_after_decide(state: Turn) -> str:
        return "search" if state.get("query") else "answer"

    graph = StateGraph(Turn)
    graph.add_node("decide_search", decide_search)
    graph.add_node("search", search)
    graph.add_node("answer", answer)
    graph.add_edge(START, "decide_search")
    graph.add_conditional_edges(
        "decide_search", route_after_decide, {"search": "search", "answer": "answer"}
    )
    graph.add_edge("search", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


# ─── Debate graph ─────────────────────────────────────────────────────
def build_debate_graph(
    seconds: float = SECONDS,
    max_turns: int = MAX_TURNS,
    *,
    emit=None,
    verbose: bool = True,
    pause: float = PAUSE_SECONDS,
):
    """Compile the orchestrator that runs the two agents against each other."""
    graphs = {
        side: build_agent_graph(side, emit=emit, verbose=verbose) for side in AGENTS
    }

    def start(state: Debate) -> dict:
        now = time.monotonic()
        if verbose:
            _line("═" * 78)
            _line(f"{BOLD} 🎭  NEURAL DEBATE · LangGraph agent vs agent{RESET}")
            _line()
            _line(f" {DIM}Motion   {RESET}{BOLD}{state.get('topic', '')}{RESET}")
            for side in ("A", "B"):
                agent = AGENTS[side]
                role = "Pro" if side == "A" else "Con"
                _line(
                    f" {DIM}{role:<8} {RESET}{_color(side)}{agent.name}{RESET} "
                    f"({agent.model} · key {_mask(agent.key)})"
                )
            _line(
                f" {DIM}Budget   {RESET}{seconds:.0f}s · max {max_turns} turns   "
                f"{DIM}LangSmith{RESET} "
                + (
                    f"{GREEN}on{RESET} ({PROJECT})"
                    if TRACING
                    else f"{YELLOW}off{RESET}"
                )
            )
            _line("═" * 78)
        return {
            "started": now,
            "deadline": now + seconds,
            "turn": 0,
            "next_side": "A",
            "transcript": [],
            "last": {},
            "searches": 0,
        }

    def route(state: Debate) -> dict:
        # Re-entry point after every turn; choose_next() does the deciding.
        return {}

    def choose_next(state: Debate) -> str:
        if state.get("turn", 0) >= max_turns:
            return "finish"
        if state.get("deadline", 0.0) - time.monotonic() < MIN_TURN_SECONDS:
            return "finish"
        return "agent_a" if state.get("next_side", "A") == "A" else "agent_b"

    def take_turn(side: str, state: Debate) -> dict:
        agent = AGENTS[side]
        other = "B" if side == "A" else "A"
        turn = state.get("turn", 0) + 1
        last = dict(state.get("last") or {})
        opponent_argument = (last.get(other) or "").strip()

        _send(
            emit,
            {
                "type": "turn_start",
                "agent": side,
                "name": agent.name,
                "turn": turn,
                "opening": not opponent_argument,
            },
        )
        if verbose:
            _line(
                f"\n{GREY}[{_stamp(state.get('started', time.monotonic()))}]{RESET} "
                f"{_color(side)}{BOLD}{agent.name}{RESET} "
                f"{DIM}· turn {turn} · {agent.stance} · "
                f"{'rebuttal' if opponent_argument else 'opening'}{RESET}"
            )

        result: dict = {}
        try:
            result = graphs[side].invoke(
                {
                    "topic": state.get("topic", ""),
                    "turn": turn,
                    "opponent_argument": opponent_argument,
                },
                config={"recursion_limit": 25},
            )
        except Exception as exc:  # noqa: BLE001 - one bad turn must not end the show
            if verbose:
                _line(f"{RED}    ✗ {agent.name} turn failed: {exc}{RESET}")

        argument = (result.get("argument") or "").strip() or (
            f"[{agent.name} produced no argument this turn]"
        )
        results = result.get("results") or []
        citations = [
            {"index": i, **r} for i, r in enumerate(results, 1) if f"[{i}]" in argument
        ]
        _send(
            emit,
            {
                "type": "turn_end",
                "agent": side,
                "name": agent.name,
                "turn": turn,
                "text": argument,
                "citations": citations,
            },
        )

        transcript = list(state.get("transcript") or [])
        transcript.append(
            {
                "turn": turn,
                "side": side,
                "name": agent.name,
                "argument": argument,
                "citations": citations,
                "search_query": result.get("query") or "",
            }
        )
        last[side] = argument

        # Give the reader time before the next agent starts speaking.
        if (
            turn < max_turns
            and state.get("deadline", 0.0) - time.monotonic()
            > MIN_TURN_SECONDS + pause
        ):
            _pause(pause, AGENTS[other].name, emit=emit, verbose=verbose)

        return {
            "turn": turn,
            "next_side": other,
            "transcript": transcript,
            "last": last,
            "searches": state.get("searches", 0) + (1 if result.get("query") else 0),
        }

    def agent_a(state: Debate) -> dict:
        return take_turn("A", state)

    def agent_b(state: Debate) -> dict:
        return take_turn("B", state)

    def finish(state: Debate) -> dict:
        elapsed = time.monotonic() - state.get("started", time.monotonic())
        transcript = state.get("transcript") or []
        words: dict[str, int] = {}
        for entry in transcript:
            words[entry["name"]] = words.get(entry["name"], 0) + len(
                entry["argument"].split()
            )

        if verbose:
            _line()
            _line("═" * 78)
            _line(
                f"{BOLD} Debate complete{RESET}  {len(transcript)} turns · {elapsed:.1f}s"
                f" · {state.get('searches', 0)} web search(es)"
            )
            for name, count in words.items():
                _line(f" {DIM}·{RESET} {name}: {count} words")
            if TRACING:
                _line(
                    f"{GREY} Traces: https://smith.langchain.com"
                    f" (project: {PROJECT}){RESET}"
                )
            _line("═" * 78)
        return {}

    graph = StateGraph(Debate)
    graph.add_node("start", start)
    graph.add_node("route", route)
    graph.add_node("agent_a", agent_a)
    graph.add_node("agent_b", agent_b)
    graph.add_node("finish", finish)

    graph.add_edge(START, "start")
    graph.add_edge("start", "route")
    graph.add_conditional_edges(
        "route",
        choose_next,
        {"agent_a": "agent_a", "agent_b": "agent_b", "finish": "finish"},
    )
    graph.add_edge("agent_a", "route")
    graph.add_edge("agent_b", "route")
    graph.add_edge("finish", END)
    return graph.compile()


def run_debate(
    topic: str,
    seconds: float = SECONDS,
    max_turns: int = MAX_TURNS,
    *,
    emit=None,
    verbose: bool = True,
    pause: float = PAUSE_SECONDS,
) -> Debate:
    graph = build_debate_graph(
        seconds, max_turns, emit=emit, verbose=verbose, pause=pause
    )
    return graph.invoke(
        {"topic": topic},
        config={"recursion_limit": max(200, int(max_turns) * 2 + 10)},
    )


def show_graphs(directory: str = "graphs") -> None:
    """Print both graphs as Mermaid and write PNGs next to the code."""
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    for name, graph in (
        ("agent_graph", build_agent_graph("A")),
        ("debate_graph", build_debate_graph()),
    ):
        _line(f"\n{BOLD}{name}{RESET}")
        _line(graph.get_graph().draw_mermaid())
        try:
            path = out / f"{name}.png"
            path.write_bytes(graph.get_graph().draw_mermaid_png())
            _line(f"{GREEN}saved {path}{RESET}")
        except Exception as exc:  # noqa: BLE001 - rendering needs network/mermaid
            _line(f"{YELLOW}png rendering unavailable: {exc}{RESET}")
