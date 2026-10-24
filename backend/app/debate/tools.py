"""Web search as a LangChain tool: Tavily first, DuckDuckGo as fallback."""

from __future__ import annotations

import logging
import os
import re

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _key() -> str:
    return (os.getenv("TAVILY_API_KEY") or "").strip().strip("'\"").strip()


def _tavily(query: str, limit: int) -> list[dict]:
    key = _key()
    if not key or key.startswith("tvly-xxxx"):
        return []
    from tavily import TavilyClient

    response = TavilyClient(api_key=key).search(
        query=query, max_results=limit, search_depth="basic"
    )
    return [
        {
            "title": (item.get("title") or "").strip(),
            "url": (item.get("url") or "").strip(),
            "snippet": (item.get("content") or "").strip(),
        }
        for item in response.get("results", [])
    ]


def _duckduckgo(query: str, limit: int) -> list[dict]:
    try:
        from ddgs import DDGS
    except ImportError:  # older package name
        from duckduckgo_search import DDGS

    with DDGS() as ddgs:
        hits = list(ddgs.text(query, max_results=limit))
    return [
        {
            "title": (hit.get("title") or "").strip(),
            "url": (hit.get("href") or hit.get("url") or "").strip(),
            "snippet": (hit.get("body") or "").strip(),
        }
        for hit in hits
    ]


def _relevant(results: list[dict], query: str) -> list[dict]:
    """Drop pages that share no meaningful word with the query."""
    words = {word.lower() for word in re.findall(r"[a-z]{4,}", query.lower())}
    if not words:
        return results
    kept = [
        result
        for result in results
        if any(
            word in f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            for word in words
        )
    ]
    return kept or results


@tool
def web_search(query: str, max_results: int = 3) -> list[dict]:
    """Search the live web for evidence, statistics and recent news.

    Returns a list of results, each with ``title``, ``url`` and ``snippet``.
    """
    limit = max(1, min(int(max_results or 3), 5))

    for provider in (_tavily, _duckduckgo):
        try:
            results = [r for r in provider(query, limit) if r.get("url")]
            results = _relevant(results, query)
            if results:
                return results[:limit]
        except Exception as exc:  # noqa: BLE001 - try the next provider
            logger.warning("%s search failed: %s", provider.__name__, exc)

    return []
