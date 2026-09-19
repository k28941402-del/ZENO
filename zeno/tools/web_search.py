"""
Web search tool — real HTTP call to DuckDuckGo's Instant Answer API
(no API key required).

Honesty note: this is an *instant-answer* API, not a full search-results
scraper. It's genuinely good for facts/definitions/well-known entities and
genuinely bad as a general web search replacement — that limitation is
real and is reported in the return value (`has_answer: False`) rather than
papered over with a fabricated result.

Like weather.py, the network call is isolated behind `fetch_fn` so tests
can inject a fake and verify parsing without a live connection.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests

_BASE_URL = "https://api.duckduckgo.com/"

FetchFn = Callable[[str, dict[str, Any]], dict[str, Any]]


def _default_fetch(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def search_instant_answer(query: str, fetch_fn: FetchFn = _default_fetch) -> dict[str, Any]:
    params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
    data = fetch_fn(_BASE_URL, params)

    abstract = data.get("AbstractText") or ""
    if abstract:
        return {
            "has_answer": True,
            "query": query,
            "answer": abstract,
            "source": data.get("AbstractURL") or "",
        }

    related = data.get("RelatedTopics") or []
    first_text = next((t.get("Text") for t in related if isinstance(t, dict) and t.get("Text")), None)
    if first_text:
        return {
            "has_answer": True,
            "query": query,
            "answer": first_text,
            "source": next((t.get("FirstURL") for t in related if isinstance(t, dict) and t.get("FirstURL")), ""),
        }

    return {
        "has_answer": False,
        "query": query,
        "answer": None,
        "source": None,
    }
