"""The Canary's tools.

Both workflow.py and agent.py import these. Identical capabilities.
The ONLY difference between the two programs is who decides the
order they run in.
"""

import os
from datetime import date
from pathlib import Path

from corpus import offline_search

# Both programs get today's date. A model has no idea what day it is,
# and "is this more than a year old?" is unanswerable without it.
# Whatever we give one, we give the other -- the ONLY difference
# between workflow.py and agent.py must be the control flow.
TODAY = date.today().strftime("%d %B %Y")

OUT_DIR = Path(__file__).parent.parent / "out"


def search(query: str) -> str:
    """Look something up. Returns a text snippet."""
    if os.environ.get("CANARY_LIVE_SEARCH") == "1":
        from ddgs import DDGS  # pip install ddgs
        hits = list(DDGS().text(query, max_results=3))
        return "\n\n".join(h["body"] for h in hits) or "No results."
    return offline_search(query)


def write_file(path: str, content: str) -> str:
    """Write text to a file under ./out/."""
    OUT_DIR.mkdir(exist_ok=True)
    target = OUT_DIR / Path(path).name
    target.write_text(content)
    return f"Wrote {len(content)} chars to out/{target.name}"


# Tool schemas, in the shape the model expects them.
# Note what these are: descriptions of functions, not the functions.
# The model never runs anything. It can only ask.

SEARCH_TOOL = {
    "name": "search",
    "description": "Search for information on a topic.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to look up."}
        },
        "required": ["query"],
    },
}

WRITE_TOOL = {
    "name": "write_file",
    "description": "Save text to a file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
}

DONE_TOOL = {
    "name": "done",
    "description": "Call this when the task is fully complete.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
        },
        "required": ["summary"],
    },
}

REGISTRY = {"search": search, "write_file": write_file}
