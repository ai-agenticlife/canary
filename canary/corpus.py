"""Offline search corpus.

Real search is non-deterministic, and a video take you can't reproduce
is a video take you can't re-record. This corpus makes every run
identical. Set CANARY_LIVE_SEARCH=1 to use real search instead
(requires: pip install ddgs).

Matching is substring-based on the whole query, so "changes" finds
"change" and "updates" finds "update". Keywords are only the words
that DISTINGUISH the two documents -- "mcp" appears in every query,
so it carries no signal and isn't listed.
"""

CORPUS = [
    {
        "topic": "when it was released",
        "keywords": [
            "release", "released", "when", "introduc", "launch",
            "announce", "created", "born", "start",
        ],
        "text": (
            "The Model Context Protocol (MCP) is an open standard for "
            "connecting AI models to tools and data sources. Anthropic "
            "introduced MCP on 25 November 2024. That is its release "
            "date; there were no earlier versions."
        ),
    },
    {
        "topic": "what changed since",
        "keywords": [
            "change", "changed", "since", "update", "new", "latest",
            "current", "spec", "deprecat", "revision", "version",
            "changelog", "history", "develop", "improve", "2026",
        ],
        "text": (
            "MCP has changed substantially since its 2024 launch. "
            "Anthropic donated MCP to the Agentic AI Foundation under "
            "the Linux Foundation in December 2025. The 2026-07-28 "
            "specification revision made the protocol stateless: the "
            "initialize handshake and Mcp-Session-Id header were "
            "removed, Multi Round-Trip Requests replaced "
            "server-initiated requests, and Roots, Sampling and "
            "Logging were deprecated with a 12-month removal window."
        ),
    },
]

NOTHING_FOUND = "No results found for that query."


def offline_search(query: str) -> str:
    """Score each document by distinctive-keyword hits, best wins."""
    q = query.lower()
    best, best_score = None, 0
    for doc in CORPUS:
        score = sum(1 for k in doc["keywords"] if k in q)
        if score > best_score:
            best, best_score = doc, score
    return best["text"] if best else NOTHING_FOUND
