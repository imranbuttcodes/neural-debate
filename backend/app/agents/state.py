"""LangGraph state model for the debate agent pipeline."""

from pydantic import BaseModel
from typing import Optional


class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str


class PreviousArgument(BaseModel):
    round_number: int
    label: str       # "Opening", "Rebuttal", "Closing"
    agent: str       # "A" or "B"
    agent_name: str  # "🦙 Llama"
    text: str


class DebateState(BaseModel):
    """Full state passed through the LangGraph pipeline."""

    # ── Inputs (set before graph runs) ─────────────────────
    topic: str
    description: str = ""
    tone: str  # roasting / comedic / aggressive / devils_advocate
    model_name: str
    agent: str       # "A" or "B"
    agent_name: str  # "🦙 Llama"
    round_number: int
    label: str       # "Opening" / "Rebuttal" / "Closing"
    position: str    # "FOR" or "AGAINST"

    # ── Memory ─────────────────────────────────────────────
    previous_arguments: list[PreviousArgument] = []

    # ── Intermediate (filled by nodes) ─────────────────────
    search_query: str = ""
    search_results: list[SearchResult] = []
    system_prompt: str = ""
    user_prompt: str = ""

    # ── Output ─────────────────────────────────────────────
    argument: str = ""
    citations: list[SearchResult] = []
    error: Optional[str] = None
