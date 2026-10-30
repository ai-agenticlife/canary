"""Canary v0 — the AGENT.

Same model. Same tools. Same task. But read this file: you cannot
tell what will happen. There is no order in here. There's a loop,
and a model that decides what goes in it, one step at a time.

The control flow does not exist until runtime.
    python agent.py "your request"
"""

import os
import sys
import time

import model
import tools

TASK = sys.argv[1] if len(sys.argv) > 1 else (
    "Find out when the Model Context Protocol was released "
    "and save it to notes.txt."
)

MAX_STEPS = 12  # Remember this line. Episode 2 is about this line.

# Raise it without editing the line above:
#   CANARY_MAX_STEPS=200 python agent.py '<something impossible>'
MAX_STEPS = int(os.environ.get("CANARY_MAX_STEPS", MAX_STEPS))

SYSTEM = (
    f"Today is {tools.TODAY}. "
    "You are a research assistant with tools. Work step by step. "
    "Trust what search returns; do not search twice for the same "
    "fact. When you save a note, include only what was asked -- no "
    "added background. Call done() when the task is fully complete."
)


def main():
    start = time.time()
    messages = [{"role": "user", "content": TASK}]
    toolset = [tools.SEARCH_TOOL, tools.WRITE_TOOL, tools.DONE_TOOL]

    for step in range(1, MAX_STEPS + 1):
        r = model.ask(messages, tools=toolset, system=SYSTEM)
        messages.append({"role": "assistant", "content": r.content})

        calls = [b for b in r.content if b.type == "tool_use"]
        if not calls:
            # The model replied with text and asked for nothing. That is not
            # the step cap -- it is the model deciding it is done, or giving
            # up. Saying "hit the cap" here would be the program lying about
            # why it stopped.
            print("\n  stopped: the model stopped asking for tools\n")
            model.report("AGENT", time.time() - start)
            return

        tin, tout = model.last_call()
        results = []
        for call in calls:
            line = f"  [{step}] {call.name}({_short(call.input)})"
            print(f"{line:<52}{tin:>7,} in {tout:>5,} out")

            if call.name == "done":
                model.report("AGENT", time.time() - start)
                print(model.growth())
                print(f"\n  finished in {step} steps")
                note = tools.OUT_DIR / "notes.txt"
                if note.exists():
                    print(f"\n--- notes.txt ---\n{note.read_text()}")
                return

            # The model asked. WE run it. This is the harness.
            output = tools.REGISTRY[call.name](**call.input)
            results.append({
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": output,
            })

        messages.append({"role": "user", "content": results})

    print(f"\n  !! hit the {MAX_STEPS}-step cap without finishing\n")
    model.report("AGENT", time.time() - start)
    print(model.growth())


def _short(d, n=30):
    s = ", ".join(f"{k}={v!r}" for k, v in d.items())
    return s[:n] + ("..." if len(s) > n else "")


if __name__ == "__main__":
    main()
