"""Canary v0 — the WORKFLOW.

Read this file top to bottom. You can see everything that will
happen, in order, without running it. The control flow lives here,
in Python, and I wrote it.

    python workflow.py "your request"
"""

import sys
import time

import model
import tools

TASK = sys.argv[1] if len(sys.argv) > 1 else (
    "Find out when the Model Context Protocol was released "
    "and save it to notes.txt."
)


def main():
    start = time.time()

    # STEP 1 — turn the request into a search query.
    r = model.ask([{
        "role": "user",
        "content": (
            f"Task: {TASK}\n\n"
            "Reply with ONLY the search query. No other text."
        ),
    }])
    query = model.text_of(r).strip()
    print(f"  [1] search query: {query}")

    # STEP 2 — search. Once.
    results = tools.search(query)
    print(f"  [2] found {len(results)} chars")

    # STEP 3 — summarise what came back.
    r = model.ask([{
        "role": "user",
        "content": (
            f"Today is {tools.TODAY}.\n"
            f"Task: {TASK}\n\n"
            f"Search results:\n{results}\n\n"
            "Write the note the task asked for. Include only what "
            "was asked -- no added background. Text only."
        ),
    }])
    note = model.text_of(r).strip()
    print(f"  [3] wrote note ({len(note)} chars)")

    # STEP 4 — save it.
    print(f"  [4] {tools.write_file('notes.txt', note)}")

    model.report("WORKFLOW", time.time() - start)
    print(model.growth())
    print(f"\n--- notes.txt ---\n{note}\n")


if __name__ == "__main__":
    main()
