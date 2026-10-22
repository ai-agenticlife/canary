# The Canary 🐤

A deliberately fragile AI agent, built one piece at a time across
season one of [AgenticLife](https://www.youtube.com/@ai.agenticlife).

It exists to be broken. Every episode adds one capability and then
wrecks it on camera, and the wreckage is what motivates the next
episode.

No framework. Plain Python. Small enough to read on screen.

---

## v0 — Episode 1: the line between a workflow and an agent

Two programs. Same model, same tools, same task, same answer.
One is an agent. One isn't.

```
canary/
  model.py      one thin wrapper around the model call
  tools.py      search + write_file, shared by both programs
  corpus.py     offline search, so runs are reproducible
  workflow.py   control flow written in Python — by me
  agent.py      control flow produced by the model — at runtime
```

**The five-word question: *who writes the control flow?***

Read `workflow.py` and you know exactly what will happen before you
run it. Read `agent.py` and you don't — there's a loop, and a model
deciding what goes in it.

### Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export CANARY_MODEL=claude-sonnet-4-5   # or whatever is current
cd canary
```

### Run them on a task that fits

```bash
python workflow.py
python agent.py
```

Both succeed. Identical output. The workflow is faster and cheaper —
one fewer model call. On a task that fits its steps, the workflow
wins.

### Now break the workflow

```bash
python workflow.py "Find out when MCP was released. If it is more \
than a year old, also find out what changed since then. Save both \
to notes.txt."
```

It does not crash. It does the four steps I wrote, searches once,
and writes a file that is **confidently, quietly incomplete**.

What it writes is better than silence, and worse in a way that is
easy to miss. It works out that MCP is more than a year old, works
out that it needs to look again, and then records that as something
it was unable to do:

> *"Since this is more than a year old, I need to find out what
> changed since then. However, the search results provided only
> contain information about the initial release date... Changes
> since release: No information available."*

It knew. It had nowhere to put that. There is no second search in
the code, so there is no second search.

That is the failure mode worth fearing. A crash is easy. Succeeding
at the wrong thing is not.

```bash
python agent.py "Find out when MCP was released. If it is more than \
a year old, also find out what changed since then. Save both to \
notes.txt."
```

The agent searches, reads the date, notices the condition, searches
again, and writes both. Nobody wrote that branch. It didn't exist
until runtime.

**About one run in fourteen, it doesn't.** It gets the release date,
reasons about the age wrong, trusts itself, skips the second search,
and writes the faulty reasoning up as though it were sound. Both
files are in `evidence/` — same headings, same confident tone, only
the numbers differ. That is measured, not estimated: 9 one-search
runs out of 50 on 22 October 2026, against 3 of 59 in August. The
difference is suggestive and not conclusive (Fisher exact p = 0.06),
which is its own lesson about quoting rates from small samples.

Reproduce it yourself:

```bash
bash variability_test.sh 40
```

### And now the part nobody says out loud

Compare the two counters. Measured on the conditional task: **four
model calls instead of two, twelve seconds instead of six, about
fifteen times the tokens.** Run it twice and it may take a different
route to the same answer — which means the run you debug is not the
run that failed.

**The agent didn't win. It traded** — flexibility bought with money,
latency, and determinism. Autonomy is a cost you pay for
flexibility you actually need.

### The cliffhanger

```python
MAX_STEPS = 12  # Remember this line. Episode 2 is about this line.
```

Raise it and give the agent something it can't finish:

```bash
CANARY_MAX_STEPS=200 python agent.py "Find out every change made to \
MCP since its release. Before you record any change, verify it with a \
separate, differently worded search. Do not call done until every \
change has been confirmed by at least three independent searches."
```

Note what *doesn't* work: asking it to predict Bitcoin's price in
2035. It correctly says it can't and stops. "Impossible" and
"unanswerable" are not the same thing. What runs away is a task
that is always *almost* done — this one reaches step 31, visibly
re-searching what it already found.

That's next week.

---

## Roadmap

| Ep | Version | Adds | Breaks |
|----|---------|------|--------|
| 1  | v0      | workflow vs. agent | an input the author never anticipated |
| 2  | v0.1    | the bare loop | it never stops |
| 3  | v0.2    | more tools | it picks the wrong one |
| 4  | v0.3    | MCP | last year's tutorial code |
| 5  | v0.4    | compaction | 50 turns without it |
| 6  | v0.5    | memory | what retrieval can't do |
| 7  | v0.6    | a second agent | two writers, one file |
| 8  | v0.7    | retries | plausible, wrong tool output |
| 9  | v0.8    | evals | passes once, fails four in ten |
| 10 | v1.0    | private data + web | exfiltration |

## Licence

MIT. Take it, break it, teach with it.
