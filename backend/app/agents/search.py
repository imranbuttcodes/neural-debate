"""Web search: DuckDuckGo primary, Tavily fallback."""

import logging
import os
from dotenv import load_dotenv

from .state import SearchResult

logger = logging.getLogger(__name__)


async def search_web(query: str, max_results: int | None = None) -> list[SearchResult]:
    """Search the web for evidence. Returns a list of SearchResult."""
    load_dotenv(override=True)
    tavily_api_key = os.getenv("TAVILY_API_KEY", "").strip()
    max_results = max_results or int(os.getenv("SEARCH_MAX_RESULTS", "3"))

    results = []

    # 1. Try DuckDuckGo first
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))

        results = [
            SearchResult(
                title=h.get("title", ""),
                snippet=h.get("body", ""),
                url=h.get("href", ""),
            )
            for h in hits
        ]
        if results:
            logger.info("Search returned %d results for: %s", len(results), query)
            return results
    except Exception as e:
        logger.warning("DDG search failed: %s", e)

    # 2. Fallback to Tavily
    if tavily_api_key and not tavily_api_key.startswith("tvly_xxxx"):
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_api_key)
            resp = client.search(query=query, max_results=max_results)
            results = [
                SearchResult(
                    title=r.get("title", ""),
                    snippet=r.get("content", ""),
                    url=r.get("url", ""),
                )
                for r in resp.get("results", [])
            ]
            logger.info("Tavily returned %d results for: %s", len(results), query)
            return results
        except Exception as e:
            logger.warning("Tavily search failed: %s", e)

    logger.warning("All search providers failed for: %s", query)
    return []
