# The Canary 🐤

A deliberately fragile AI agent, built one piece at a time across
season one of [AgenticLife](https://www.youtube.com/@ai.agenticlife).

It exists to be broken. Every episode adds one capability, then wrecks it
on camera, and the wreckage is what motivates the next episode.

No framework. Plain Python. Small enough to read on screen.

**Every number below is measured, and the thing that produced it is in
this repo.** Where a measurement contradicts something an episode already
said, the correction is in [Corrections](#corrections) rather than quietly
edited away.

---

## Giving it 15 tools instead of 3 didn't make it worse

**120 runs. 120 correct. No degradation at any tool count we tested.**

"More tools makes an agent dumber" is repeated constantly. It hides two
separate claims — that the *count* hurts, and that overlapping
*descriptions* hurt — so there are three toolsets here, not two:

| | tools | what it is |
|---|---|---|
| `small` | 3 | search, write_file, done |
| `real` | 15 | plus twelve a working developer would actually add |
| `muddy` | 15 | plus twelve written to collide — six ways to say "search" |

Every tool in `real` is genuinely implemented. A tool that returns "not
available" fails for reasons that have nothing to do with tool count.

### Experiment one — 60 runs

| condition | correct | median steps | call one | whole run |
|---|---|---|---|---|
| `small` | 20/20 | 4 | 770 | 4,080 |
| `real` | 20/20 | 4 | 1,444 | 6,780 |
| `muddy` | 20/20 | 4 | 1,477 | 6,909 |

Not just the same score — the same path. `search, search, write_file,
done`, every run, in every condition. Even with six colliding ways to say
"search", it reached for an appropriate one 18 times out of 20.

### Experiment two — the hole in experiment one

All six `muddy` search tools returned the same corpus, so there was no
wrong tool to pick. Picking badly cost nothing, which means experiment one
*could not have detected* a bad choice. That is not a result, it is a
broken instrument.

So we split them: a different, narrower body of text behind each. The news
search genuinely cannot answer a spec question and the docs search
genuinely cannot answer a release-date question. Neither half is wrong;
each is partial.

**Another 60 runs. Still 20/20, 20/20, 20/20.** The median `muddy` run
didn't move: 4 steps, 6,914 tokens against 6,909 before.

But **2 runs out of 20 thrashed** — one to 11 steps and 23,378 tokens, 3.4×
the median, taking eight searches to do a two-search job. It still got the
right answer. It just paid 3.4× for it.

**That tail is not statistically significant.** 2 of 20 against 0 of 20 is
a two-sided Fisher exact p of 0.487. Run it again and it might be zero, or
four. It is a signal worth chasing, not a finding.

### What did change: the bill

```
call one      770  ->  1,444      +674   +88%
whole run   4,080  ->  6,780    +2,699   +66%
```

**56 tokens for each of twelve tools the run never called**, on every
single call.

Pricing each definition by leave-one-out — removing one tool from the full
set, rather than adding one to an empty set, which wrongly charges it for
the fixed cost of having tools at all:

```
having any tools at all (fixed)   497
get_date                           42     word_count        56
list_files                         45     read_file         57
calculate                          51     fetch_url         58
done                               54     search            61
search_docs                        54     write_file        66
search_news                        55     summarize         71
delete_file                        55     append_file       74
extract_dates                      56
```

Cheapest to dearest is a factor of 1.8. Same model, same encoder — the only
difference is how much was written. And it reconciles exactly, both ways:

```
497 fixed + 855 definitions + 92 task/system = 1,444   (15 tools)
497 fixed + 181 definitions + 92 task/system =   770   ( 3 tools)
```

**94% of the first call is tool scaffolding.**

### Why nothing degraded — the part that matters

Before calling the claim wrong, we went looking for its strongest version.
[Anthropic's own write-up on advanced tool
use](https://www.anthropic.com/research/advanced-tool-use) says the problem
starts when **tool definitions pass 10,000 tokens**, and lists "small tool
library (<10 tools)" and "tool definitions are compact" under *less
beneficial*.

Our fifteen definitions are **855 tokens**. We had built their control
group by accident. At the scale where they measure it, the effect is not
subtle — they report tool-selection accuracy going from 49% to 74% with
on-demand tool loading enabled.

Then the arithmetic on their published per-server numbers:

| | tools | tokens | per tool |
|---|---|---|---|
| GitHub MCP | 35 | ~26K | **~740** |
| Slack MCP | 11 | ~21K | **~1,900** |
| ours | 15 | 855 | **57** |

Real MCP tool definitions are **13× to 33× heavier** than hand-written
ones. Eleven Slack tools cost what 368 of ours would.

**So it was never the count. It is the weight.** We didn't disprove
anything — we found the floor, and found out our tools were too small to
reach the problem.

### Reproduce it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export CANARY_MODEL=claude-sonnet-4-5

python measure_tools.py --smoke        # calls all 27 tools, no model
python measure_tools.py --dry-run      # the loop, with a fake model
python measure_tools.py 20             # the real thing: 60 runs
python measure_tools.py 20 --split     # experiment two
```

Or read back the runs this repo was cut from, without spending anything:

```bash
python show.py evidence/tools-20261030-160427.json
python show.py evidence/tools-20261030-160427.json --bill
python show.py evidence/tools-split-20261107-112239.json \
       evidence/tools-20261030-160427.json --worst
```

**Caveats, stated plainly:** one task, one model
(`claude-sonnet-4-5`), one offline corpus, n=20 per condition, 15 tools and
855 tokens of definitions — an order of magnitude under the scale where the
published numbers say this starts to bite. Do not read this as "tool count
never matters." Read it as "at this scale, on this task, it didn't, and
here is the scale at which it does."

Episode: *[I Gave My Agent 15 Tools To Make It Dumber. It
Didn't.](https://www.youtube.com/watch?v=WPjWN4U17Rw)*

---

## Every turn through the loop costs more than the last

An agent runs in a loop. The conversation you send grows; the reply you get
back doesn't.

Twenty-five calls, measured per call:

| | in | out |
|---|---|---|
| call 1 | 793 | 90 |
| call 5 | 1,318 | — |
| call 10 | 2,105 | — |
| call 25 | 4,168 | 56 |

Input grew **5.26×**. Output never did: mean 65, range 56–90, trend −0.6 a
step with R² 0.18 — flat.

A straight line fits the input at **R² 0.99791**. A quadratic buys
0.0012% more. Within the length of this run, growth is linear, and the
bill is the area under that line, not the height of it: 25 calls cost
62,120 input tokens against 19,825 if every call had looked like the
first — **3.13×**. Double the steps from 12 to 24 and the cost goes up
3.11×, not 2×.

```bash
python measure_growth.py 25
python measure_call_one.py
```

Episode: *[The Loop](https://www.youtube.com/watch?v=MAML_iymWj8)*

---

## The line between a workflow and an agent

Two programs. Same model, same tools, same task, same answer. One is an
agent. One isn't.

```
canary/
  model.py      one thin wrapper around the model call
  tools.py      search + write_file, shared by both programs
  corpus.py     offline search, so runs are reproducible
  workflow.py   control flow written in Python — by me
  agent.py      control flow produced by the model — at runtime
```

**The five-word question: _who writes the control flow?_**

Read `workflow.py` and you know exactly what will happen before you run it.
Read `agent.py` and you don't — there's a loop, and a model deciding what
goes in it.

```bash
cd canary
python workflow.py
python agent.py
```

Both succeed. Identical output. The workflow is faster and cheaper — one
fewer model call. **On a task that fits its steps, the workflow wins.**

### Now break the workflow

```bash
python workflow.py "Find out when MCP was released. If it is more \
than a year old, also find out what changed since then. Save both \
to notes.txt."
```

It does not crash. It does the four steps that were written, searches
once, and writes a file that is **confidently, quietly incomplete**:

> *"Since this is more than a year old, I need to find out what changed
> since then. However, the search results provided only contain
> information about the initial release date... Changes since release: No
> information available."*

It knew. It had nowhere to put that. There is no second search in the
code, so there is no second search. A crash is easy. Succeeding at the
wrong thing is not.

The agent, given the same task, searches, reads the date, notices the
condition, searches again, and writes both. Nobody wrote that branch; it
didn't exist until runtime.

**About one run in fourteen, it doesn't.** It gets the release date,
reasons about the age wrong, trusts itself, skips the second search, and
writes the faulty reasoning up as though it were sound. Both files are in
`evidence/` — same headings, same confident tone, only the numbers differ.
Measured, not estimated: 9 one-search runs out of 50 on 22 October 2026,
against 3 of 59 in August. Suggestive, not conclusive (Fisher exact
p = 0.06), which is its own lesson about quoting rates from small samples.

```bash
bash variability_test.sh 40
```

And the part nobody says out loud: on the conditional task the agent took
**four model calls instead of two, twelve seconds instead of six, about
fifteen times the tokens** — and may take a different route on a rerun,
which means the run you debug is not the run that failed. The agent didn't
win. It traded.

Episode: *[What Is Agentic AI? The Line Nobody
Draws](https://www.youtube.com/watch?v=5-FW_go0l9k)*

---

## Corrections

Episode 2 put this breakdown of its first call on screen at 3:01:

| | published | measured |
|---|---|---|
| the question | **24** tokens, 3% | **52** tokens, 7% |
| the system prompt | 63 tokens, 8% | 63 — right |
| the tools | **706** tokens, 89% | **678** tokens, 85% |

Both add to 793, which is the whole problem.

**706 was never measured.** It is 793 − 24 − 63. The 793 came from a long
multi-sentence task; the 24 came from a different script running a short
default task; the third number was a residual computed to reconcile two
different runs. The total closed, so nothing caught it.

The corrected figures stand on their own: 678 is the 497-token fixed
overhead plus 181 for three definitions, measured by leave-one-out.
52 + 63 + 678 = 793.

**The rule that broke: every number on screen has to come from the run
that is on screen.** A derived figure sitting beside measured ones is the
failure mode, and a total that adds up is not evidence — it is what hides
the error.

---

## Roadmap

Hypotheses, not scripts. Episode 3's predicted break — "it picks the wrong
one" — didn't happen, and shipping the null result was the episode.

| Ep | Version | Adds | Expected break | Outcome |
|---|---|---|---|---|
| 1 | v0 | workflow vs. agent | an input the author never anticipated | confirmed |
| 2 | v0.1 | the bare loop | it never stops | confirmed |
| 3 | v0.2 | more tools | it picks the wrong one | **didn't** — 120/120 |
| 4 | v0.3 | MCP | last year's tutorial code | — |
| 5 | v0.4 | compaction | 50 turns without it | — |
| 6 | v0.5 | memory | what retrieval can't do | — |
| 7 | v0.6 | a second agent | two writers, one file | — |
| 8 | v0.7 | retries | plausible, wrong tool output | — |
| 9 | v0.8 | evals | passes once, fails four in ten | — |
| 10 | v1.0 | private data + web | exfiltration | — |

## Licence

MIT. Take it, break it, teach with it.

If you find a number here that doesn't reproduce, open an issue — that
correction goes on camera in the next episode.
