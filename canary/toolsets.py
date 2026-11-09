"""Three toolsets for episode 3, and the honest difference between them.

The claim under test is "giving an agent more tools makes it dumber". That
sentence hides two different claims, and almost everyone who repeats it
has not separated them:

    1. the COUNT hurts    -- fifteen tools is worse than three, full stop
    2. the DESCRIPTIONS hurt -- fifteen tools that overlap is worse than
       fifteen that don't, and count has little to do with it

So there are three toolsets here, not two.

    SMALL   the three tools episodes 1 and 2 used
    REAL    SMALL + twelve a working developer would actually add.
            They overlap where real toolsets overlap -- search_news and
            search_docs genuinely compete with search, the way a real MCP
            server's tools do. Nothing here is written to trip the model.
    MUDDY   SMALL + twelve whose descriptions deliberately collide. Six
            ways to say "search", six ways to say "save".

MUDDY exists as a control, not as the demo. If REAL degrades, MUDDY tells
us whether that was about the number or about the writing. If REAL does
not degrade, MUDDY tells us the effect needs bad descriptions to appear at
all -- which is a more useful finding than the one everyone repeats.

Every tool in REAL is really implemented. A tool that returns "not
available" would make the agent fail for a reason that has nothing to do
with tool count, and that would be a rigged result.
"""

import re
from datetime import date
from pathlib import Path

import tools as base
from corpus import offline_search

OUT_DIR = base.OUT_DIR


def _schema(name, description, props, required):
    return {"name": name, "description": description,
            "input_schema": {"type": "object", "properties": props,
                             "required": required}}


# ---------------------------------------------------------------- REAL --
# Twelve tools a developer building a research agent would plausibly add.
# They work. Where they overlap with search, they overlap the way real
# toolsets do, because someone added a specialised one later.

def fetch_url(url: str) -> str:
    """Offline, a URL is just another query against the same corpus."""
    return offline_search(url.replace("/", " ").replace("-", " "))


def read_file(path: str) -> str:
    p = OUT_DIR / Path(path).name
    return p.read_text() if p.exists() else f"No such file: {path}"


def list_files() -> str:
    if not OUT_DIR.exists():
        return "out/ is empty"
    names = sorted(p.name for p in OUT_DIR.iterdir() if p.is_file())
    return "\n".join(names) if names else "out/ is empty"


def append_file(path: str, content: str) -> str:
    OUT_DIR.mkdir(exist_ok=True)
    p = OUT_DIR / Path(path).name
    with p.open("a") as f:
        f.write(content)
    return f"Appended {len(content)} chars to out/{p.name}"


def delete_file(path: str) -> str:
    p = OUT_DIR / Path(path).name
    if not p.exists():
        return f"No such file: {path}"
    p.unlink()
    return f"Deleted out/{p.name}"


def get_date() -> str:
    return date.today().strftime("%d %B %Y")


def calculate(expression: str) -> str:
    if not re.fullmatch(r"[0-9+\-*/(). ]+", expression or ""):
        return "Only arithmetic is supported."
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:                       # noqa: BLE001
        return f"Could not evaluate: {e}"


def word_count(text: str) -> str:
    return str(len(text.split()))


def extract_dates(text: str) -> str:
    pat = (r"\b(\d{1,2}\s+[A-Z][a-z]+\s+\d{4}"
           r"|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}"
           r"|\d{4}-\d{2}-\d{2})\b")
    hits = re.findall(pat, text or "")
    return "\n".join(hits) if hits else "No dates found."


def summarize(text: str, max_words: int = 40) -> str:
    words = (text or "").split()
    return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")


# Experiment 1 could not detect a bad tool choice, because search_news and
# search_docs both returned the whole corpus -- there was no wrong tool to
# pick. SPLIT puts a different, narrower body of text behind each one, so
# reaching for the wrong search costs a step.
#
# This is not rigging. A real news search genuinely would not surface a
# protocol's 2024 release date, and a real docs search genuinely would
# return the spec revision. Both sub-corpora are true extracts of the same
# facts; neither is wrong, each is partial.
SPLIT = False

_NEWS = ("Anthropic donated the Model Context Protocol to the Agentic AI "
         "Foundation under the Linux Foundation in December 2025, handing "
         "stewardship of the standard to a neutral body.")
_DOCS = ("The 2026-07-28 specification revision made MCP stateless: the "
         "initialize handshake and Mcp-Session-Id header were removed, "
         "Multi Round-Trip Requests replaced server-initiated requests, "
         "and Roots, Sampling and Logging were deprecated with a "
         "12-month removal window.")


def search(query: str) -> str:
    """The general tool. Always able to answer either half of the task."""
    return base.search(query)


def search_news(query: str) -> str:
    return _NEWS if SPLIT else offline_search(query)


def search_docs(query: str) -> str:
    return _DOCS if SPLIT else offline_search(query)


def _muddy_backend(i):
    """With SPLIT on, the six identical-sounding aliases do NOT do the same
    thing. That is the realistic nightmare: descriptions that cannot
    disambiguate, behind tools that behave differently."""
    def fn(query, **_):
        if not SPLIT:
            return offline_search(query)
        return (offline_search(query), _NEWS, _DOCS)[i % 3]
    return fn


REAL_EXTRA = [
    (_schema("fetch_url", "Fetch the contents of a web page by URL.",
             {"url": {"type": "string"}}, ["url"]), fetch_url),
    (_schema("read_file", "Read a file previously written to ./out/.",
             {"path": {"type": "string"}}, ["path"]), read_file),
    (_schema("list_files", "List the files in ./out/.", {}, []), list_files),
    (_schema("append_file", "Append text to the end of a file in ./out/.",
             {"path": {"type": "string"}, "content": {"type": "string"}},
             ["path", "content"]), append_file),
    (_schema("delete_file", "Delete a file from ./out/.",
             {"path": {"type": "string"}}, ["path"]), delete_file),
    (_schema("get_date", "Get today's date.", {}, []), get_date),
    (_schema("calculate", "Evaluate an arithmetic expression.",
             {"expression": {"type": "string"}}, ["expression"]), calculate),
    (_schema("word_count", "Count the words in a piece of text.",
             {"text": {"type": "string"}}, ["text"]), word_count),
    (_schema("extract_dates", "Find calendar dates in a piece of text.",
             {"text": {"type": "string"}}, ["text"]), extract_dates),
    (_schema("summarize", "Shorten a piece of text to its first N words.",
             {"text": {"type": "string"},
              "max_words": {"type": "integer"}}, ["text"]), summarize),
    (_schema("search_news", "Search recent news articles for a topic.",
             {"query": {"type": "string"}}, ["query"]), search_news),
    (_schema("search_docs", "Search technical documentation for a topic.",
             {"query": {"type": "string"}}, ["query"]), search_docs),
]

# --------------------------------------------------------------- MUDDY --
# The same count, written badly on purpose. Six ways to say "search", six
# ways to say "save". This is the control that tells us whether a REAL
# result was about the number of tools or about how they were written.

_MUDDY_SEARCH = [
    ("lookup", "Search for information on a topic."),
    ("find_info", "Find information about something."),
    ("query_knowledge", "Query for information on a subject."),
    ("research", "Research a topic and return information."),
    ("web_search", "Search for information on a topic."),
    ("fetch_facts", "Retrieve information about a topic."),
]
_MUDDY_SAVE = [
    ("save", "Save text to a file."),
    ("store", "Store text in a file."),
    ("record", "Record text to a file."),
    ("persist", "Write text out to a file."),
    ("output_file", "Save text to a file."),
    ("create_document", "Create a file containing text."),
]

MUDDY_EXTRA = (
    # The parameter names here must match the schema's property names
    # exactly -- the loop calls fn(**call.input), so `query` in the schema
    # means `query` in the signature. An earlier version used `q` and all
    # six of these raised TypeError the moment the model picked one.
    [(_schema(n, d, {"query": {"type": "string"}}, ["query"]),
      _muddy_backend(i))
     for i, (n, d) in enumerate(_MUDDY_SEARCH)]
    + [(_schema(n, d, {"path": {"type": "string"},
                       "content": {"type": "string"}}, ["path", "content"]),
        (lambda path, content, **_: base.write_file(path, content)))
       for n, d in _MUDDY_SAVE]
)

# --------------------------------------------------------------- build --

SMALL = [base.SEARCH_TOOL, base.WRITE_TOOL, base.DONE_TOOL]
_CORE_REGISTRY = {"search": search, "write_file": base.write_file}


def build(name):
    """-> (schemas, registry).  `done` is handled by the loop, not here."""
    if name == "small":
        return list(SMALL), dict(_CORE_REGISTRY)
    extra = REAL_EXTRA if name == "real" else MUDDY_EXTRA
    schemas = [base.SEARCH_TOOL, base.WRITE_TOOL]
    reg = dict(_CORE_REGISTRY)
    for sch, fn in extra:
        schemas.append(sch)
        reg[sch["name"]] = fn
    schemas.append(base.DONE_TOOL)          # done stays last in every set
    return schemas, reg


CONDITIONS = ("small", "real", "muddy")

# Which tools are a way of searching, in any condition. The experiment
# counts these, because an extra search is what a bad pick costs you.
SEARCH_TOOLS = ({"search", "search_news", "search_docs"}
                | {n for n, _ in _MUDDY_SEARCH})

if __name__ == "__main__":
    import sys, textwrap
    if "--split" in sys.argv:
        SPLIT = True
    print(f"\n  SPLIT = {SPLIT}\n")
    for c in CONDITIONS:
        s, _ = build(c)
        names = ", ".join(t["name"] for t in s)
        print(f"  {c:<7} {len(s):>2} tools")
        # wrapped, because fifteen tool names on one line is 188 columns and
        # unreadable in a terminal -- and unreadable on screen, which is
        # where this ends up
        for line in textwrap.wrap(names, 60):
            print(f"           {line}")
        print()
