"""LangGraph debate agent: search → tone → llm → format."""

import logging
from typing import Any, Callable, Coroutine

from langchain_core.messages import HumanMessage, SystemMessage

from .llm import get_llm
from .search import search_web
from .state import DebateState, SearchResult
from .tones import build_prompts

logger = logging.getLogger(__name__)


async def run_debate_agent(
    state: DebateState,
    token_callback: Callable[[str], Coroutine[Any, Any, None]] | None = None,
) -> DebateState:
    """
    Run the full debate agent pipeline for one turn.

    Instead of a full LangGraph StateGraph (which adds complexity for 4 linear
    nodes), this uses a simple async pipeline — same logic, less boilerplate.

    Args:
        state: The current debate state with inputs filled in.
        token_callback: Async function called with each streamed token.

    Returns:
        Updated DebateState with argument + citations filled.
    """

    # ── 1. Search ──────────────────────────────────────────────────
    query = f"{state.topic} {state.label}"
    state.search_query = query
    try:
        state.search_results = await search_web(query)
    except Exception as e:
        logger.warning("Search failed: %s", e)
        state.search_results = []

    # ── 2. Build prompts ───────────────────────────────────────────
    system_prompt, user_prompt = build_prompts(state)
    state.system_prompt = system_prompt
    state.user_prompt = user_prompt

    # ── 3. Stream from LLM ────────────────────────────────────────
    llm = get_llm(state.model_name, streaming=True)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    accumulated = ""
    try:
        async for chunk in llm.astream(messages):
            raw_token = chunk.content
            token_str = raw_token if isinstance(raw_token, str) else str(raw_token or "")
            if token_str:
                accumulated += token_str
                if token_callback:
                    await token_callback(token_str)
    except Exception as e:
        logger.error("LLM streaming failed: %s", e)
        state.error = str(e)
        # Try fallback without streaming
        try:
            response = await llm.ainvoke(messages)
            raw_resp = response.content
            accumulated = raw_resp if isinstance(raw_resp, str) else str(raw_resp or "")
        except Exception as e2:
            logger.error("LLM fallback also failed: %s", e2)
            state.error = str(e2)
            accumulated = "I encountered an error generating my argument. The show must go on!"

    state.argument = accumulated

    # ── 4. Match citations ─────────────────────────────────────────
    matched = []
    for i, sr in enumerate(state.search_results):
        ref = f"[{i + 1}]"
        if ref in accumulated:
            matched.append(sr)
    # If no explicit refs found, include all search results anyway
    state.citations = matched if matched else state.search_results

    return state
