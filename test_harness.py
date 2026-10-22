"""Offline test of the Canary harness — no API key, no network.

Stubs the anthropic SDK and scripts the model's replies so we can
verify the loop, tool dispatch, message shapes and the done path.

    python test_harness.py
"""
import sys, types
from types import SimpleNamespace

# --- stub the anthropic SDK -------------------------------------
fake = types.ModuleType("anthropic")
SCRIPT = []          # queue of responses to hand back
SENT = []            # every kwargs dict we were called with


class _Messages:
    def create(self, **kw):
        SENT.append(kw)
        return SCRIPT.pop(0)


class Anthropic:
    def __init__(self, *a, **k):
        self.messages = _Messages()


fake.Anthropic = Anthropic
sys.modules["anthropic"] = fake
sys.path.insert(0, "canary")

import model, tools, agent  # noqa: E402


def txt(s):
    return SimpleNamespace(type="text", text=s)


def use(name, inp, id_="tu_1"):
    return SimpleNamespace(type="tool_use", name=name, input=inp, id=id_)


def resp(*blocks):
    return SimpleNamespace(
        content=list(blocks),
        usage=SimpleNamespace(input_tokens=100, output_tokens=40),
    )


# --- script a two-search run, exactly the episode-1 break --------
SCRIPT.extend([
    resp(txt("Let me look that up."),
         use("search", {"query": "Model Context Protocol released"}, "a")),
    resp(txt("Nov 2024 — over a year. Checking what changed."),
         use("search", {"query": "what changed in MCP since 2024"}, "b")),
    resp(use("write_file", {"path": "notes.txt", "content": "both facts"}, "c")),
    resp(use("done", {"summary": "saved both"}, "d")),
])

agent.TASK = "Find out when MCP was released; if over a year old, also find what changed."
agent.main()

# --- assertions -------------------------------------------------
assert model.CALLS == 4, f"expected 4 model calls, got {model.CALLS}"
assert len(SENT) == 4

# every tool result must be handed back as a user turn.
# check the FINAL call — its message list is the accumulated history.
tool_results = [
    b for m in SENT[-1]["messages"]
    if isinstance(m["content"], list)
    for b in m["content"]
    if isinstance(b, dict) and b.get("type") == "tool_result"
]
assert len(tool_results) == 3, f"expected 3 tool_results, got {len(tool_results)}"
assert all(r["tool_use_id"] in {"a", "b", "c"} for r in tool_results)

# the harness, not the model, executed the tools
out = (tools.OUT_DIR / "notes.txt").read_text()
assert out == "both facts", out

# the system prompt and toolset were passed on every call
assert all(kw.get("system") for kw in SENT)
assert all(len(kw["tools"]) == 3 for kw in SENT)

print("\n[PASS] harness executes tools, threads results, honours done()")

# --- the step cap actually fires --------------------------------
model.CALLS = 0
SCRIPT.clear()
SENT.clear()
for i in range(agent.MAX_STEPS):
    SCRIPT.append(resp(use("search", {"query": f"loop {i}"}, f"x{i}")))
agent.main()
assert model.CALLS == agent.MAX_STEPS, model.CALLS
print(f"[PASS] step cap stops a non-terminating agent at {agent.MAX_STEPS}")
