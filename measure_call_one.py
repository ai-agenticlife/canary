#!/usr/bin/env python3
"""What is actually in the agent's first call?

Episode 2 says call one costs ~763 tokens for a one-sentence question,
and that the rest is the system prompt plus the tool schemas. That is a
claim about a specific number, so it gets measured, not reasoned about.

Method: count the same request with pieces removed, and difference them.
Uses the token-counting endpoint if the SDK has it, otherwise makes real
calls with max_tokens=1 and reads usage.input_tokens -- same answer,
costs a fraction of a cent.

    python3 measure_call_one.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "canary"))

import model, tools                                    # noqa: E402

TASK = ("Find out when the Model Context Protocol was released "
        "and save it to notes.txt.")
SYSTEM = (f"Today is {tools.TODAY}. "
          "You are a research assistant with tools. Work step by step. "
          "Trust what search returns; do not search twice for the same "
          "fact. When you save a note, include only what was asked -- no "
          "added background. Call done() when the task is fully complete.")
MSGS = [{"role": "user", "content": TASK}]
ALL = [tools.SEARCH_TOOL, tools.WRITE_TOOL, tools.DONE_TOOL]


def count(system=None, toolset=None):
    kw = {"model": model.MODEL, "messages": MSGS}
    if system:
        kw["system"] = system
    if toolset:
        kw["tools"] = toolset
    try:
        return model.client.messages.count_tokens(**kw).input_tokens
    except (AttributeError, TypeError):
        kw["max_tokens"] = 1
        return model.client.messages.create(**kw).usage.input_tokens


bare = count()
with_sys = count(system=SYSTEM)
full = count(system=SYSTEM, toolset=ALL)

print(f"\nCALL ONE, BROKEN DOWN   (model: {model.MODEL})\n")
rows = [("the question itself", bare),
        ("+ system prompt", with_sys - bare),
        ("+ all three tool schemas", full - with_sys)]
for label, v in rows:
    print(f"  {label:<32}{v:>7,}")
print(f"  {'':-<32}{'':->7}")
print(f"  {'total for call one':<32}{full:>7,}")

# Measuring a tool by ADDING it to an empty set is wrong: the API injects
# its own tool-use instructions as soon as any tool is present, and that
# fixed cost lands on whichever tool went first. Measure each one by
# REMOVING it from the full set instead -- the overhead is in both sides
# and cancels.
print("\n  each tool, measured by removing it from the full set:")
marginal = {}
for t in ALL:
    without = [x for x in ALL if x is not t]
    marginal[t["name"]] = full - count(system=SYSTEM, toolset=without)
    print(f"    {t['name']:<30}{marginal[t['name']]:>7,}")

per_tool = sum(marginal.values())
overhead = (full - with_sys) - per_tool
print(f"    {'':-<30}{'':->7}")
print(f"    {'three schemas':<30}{per_tool:>7,}")
print(f"    {'tool-use overhead (fixed)':<30}{overhead:>7,}")

avg = per_tool / len(ALL)
print(f"\n  the question is {bare/full*100:.0f}% of call one.")
print(f"  {(full - bare)/full*100:.0f}% ({full - bare:,} tokens) is scaffolding,")
print(f"  and all of it is sent again on every single call.")
print(f"\n  EXTRAPOLATION FOR EPISODE 3")
print(f"  fixed cost of having tools at all:  {overhead:,}")
print(f"  average schema:                     {avg:,.0f}")
for n in (3, 5, 10, 15):
    print(f"  {n:>2} tools would cost roughly        "
          f"{overhead + avg*n:,.0f} tokens per call")
print(f"\n  NOTE: naively multiplying call one by five would predict "
      f"{(full - with_sys)*5:,.0f}")
print(f"  for fifteen tools. That is wrong -- it charges the fixed "
      f"overhead five times.")
