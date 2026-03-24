# Copyright (c) 2025-2026 Yutaro Maeda. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Web search module for claim verification using DuckDuckGo."""

from __future__ import annotations

from duckduckgo_search import DDGS

from uradori.models import Source


def search_claim(claim_text: str, max_results: int = 5) -> list[Source]:
    """Search the web for evidence related to a claim.

    Uses DuckDuckGo (no API key required) to find relevant sources.

    Args:
        claim_text: The factual claim to search for.
        max_results: Maximum number of search results.

    Returns:
        List of Source objects with search results.
    """
    sources: list[Source] = []

    try:
        with DDGS() as ddgs:
            results = ddgs.text(
                keywords=claim_text,
                max_results=max_results,
                safesearch="moderate",
            )

        for result in results:
            sources.append(
                Source(
                    title=result.get("title", ""),
                    url=result.get("href", ""),
                    snippet=result.get("body", ""),
                )
            )
    except Exception:
        # DuckDuckGo can be flaky; return empty list rather than crash
        pass

    return sources


def search_claim_news(claim_text: str, max_results: int = 3) -> list[Source]:
    """Search news specifically for a claim.

    Args:
        claim_text: The factual claim to search for.
        max_results: Maximum number of news results.

    Returns:
        List of Source objects from news search.
    """
    sources: list[Source] = []

    try:
        with DDGS() as ddgs:
            results = ddgs.news(
                keywords=claim_text,
                max_results=max_results,
            )

        for result in results:
            sources.append(
                Source(
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    snippet=result.get("body", ""),
                )
            )
    except Exception:
        pass

    return sources
