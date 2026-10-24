"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel
from typing import Optional


# ── Debate ─────────────────────────────────────────────────────────

class DebateCreate(BaseModel):
    topic: str
    description: str = ""
    tone: str = "roasting"
    duration_secs: int = 300


class AgentInfo(BaseModel):
    name: str
    model: str


class DebateCreateResponse(BaseModel):
    debate_id: int
    invite_url: str
    creator_token: str
    agent_a: AgentInfo
    agent_b: AgentInfo


class DebateResponse(BaseModel):
    id: int
    topic: str
    description: str
    tone: str
    agent_a_name: str
    agent_b_name: str
    model_a: str
    model_b: str
    duration_secs: int
    status: str
    created_at: str
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    winner: Optional[str] = None


class DebateStartResponse(BaseModel):
    status: str
    ends_at: str


# ── Viewer ─────────────────────────────────────────────────────────

class ViewerCreate(BaseModel):
    debate_id: int
    display_name: str
    avatar_emoji: str


class ViewerResponse(BaseModel):
    viewer_id: str
    debate_id: int
    display_name: str
    avatar_emoji: str


# ── Vote ───────────────────────────────────────────────────────────

class VoteCreate(BaseModel):
    debate_id: int
    vote: str  # "A" or "B"


class VoteCounts(BaseModel):
    A: int = 0
    B: int = 0
    total: int = 0
    percent_A: float = 0.0
    percent_B: float = 0.0


class VoteResponse(BaseModel):
    ok: bool
    A: int
    B: int
    total: int


# ── Snapshot (for reconnect / late join) ───────────────────────────

class RoundSnapshot(BaseModel):
    round: int
    label: str
    agent: str
    argument: str
    citations: list = []


class StateSnapshot(BaseModel):
    debate: DebateResponse
    rounds_so_far: list[RoundSnapshot] = []
    current_vote_counts: VoteCounts = VoteCounts()
    viewer_vote: Optional[str] = None
