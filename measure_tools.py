#!/usr/bin/env python3
"""Episode 3's experiment: does giving an agent more tools make it worse?

Everyone says yes. Nobody separates the two claims hiding inside it --
that the NUMBER of tools hurts, and that OVERLAPPING DESCRIPTIONS hurt.
So this runs three conditions on the same task with the same model:

    small   3 tools   the set episodes 1 and 2 used
    real   15 tools   + twelve a developer would actually add, overlapping
                      only where real toolsets overlap
    muddy  15 tools   + twelve written to collide on purpose

`muddy` is the control. If `real` degrades, `muddy` says whether that was
about the count or the writing. If `real` does not degrade, that is the
finding, and it is a more interesting one than the thing everyone repeats.

    python3 measure_tools.py            # 20 runs per condition
    python3 measure_tools.py 10         # fewer
    python3 measure_tools.py --dry-run  # no API calls; checks the harness

Writes evidence/tools-<timestamp>.json and prints the summary that the
script has to be written against. Nothing goes on camera that is not in
that file.
"""
import collections, json, math, os, random, re, sys, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "canary"))

import model, tools, toolsets                                # noqa: E402

TASK = ("Find out when the Model Context Protocol was released and what "
        "has changed since. Save both to notes.txt.")

SYSTEM = (
    f"Today is {tools.TODAY}. "
    "You are a research assistant with tools. Work step by step. "
    "Trust what search returns; do not search twice for the same "
    "fact. When you save a note, include only what was asked -- no "
    "added background. Call done() when the task is fully complete."
)

MAX_STEPS = 12
IDEAL_STEPS = 4          # search, search, write, done

# The oracle. The corpus holds exactly two documents, so a correct answer
# needs both of them -- that is what makes this task able to fail.
RELEASED = re.compile(r"(25\s+Nov|Nov\w*\s+25|2024-11-25)", re.I)
CHANGED = re.compile(r"(agentic ai foundation|linux foundation|"
                     r"2026-07-28|stateless|deprecat)", re.I)


# ----------------------------------------------------------- statistics --
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def fisher(a, b, c, d):
    """Two-sided Fisher exact on [[a,b],[c,d]]. No scipy on the box."""
    def lf(n):
        return math.lgamma(n + 1)

    def p(a_, b_, c_, d_):
        return math.exp(lf(a_ + b_) + lf(c_ + d_) + lf(a_ + c_) + lf(b_ + d_)
                        - lf(a_) - lf(b_) - lf(c_) - lf(d_) - lf(a_ + b_ + c_ + d_))
    obs = p(a, b, c, d)
    tot = 0.0
    n = a + b + c + d
    for i in range(0, min(a + b, a + c) + 1):
        j, k, l = a + b - i, a + c - i, d - a + i
        if min(j, k, l) < 0:
            continue
        q = p(i, j, k, l)
        if q <= obs * (1 + 1e-9):
            tot += q
    return min(1.0, tot)


def med(xs):
    xs = sorted(xs)
    if not xs:
        return 0
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


# ------------------------------------------------------------- the run --
class FakeResponse:
    def __init__(self, blocks, tin, tout):
        self.content = blocks
        self.usage = type("U", (), {"input_tokens": tin, "output_tokens": tout})


class Block:
    def __init__(self, name=None, inp=None, text=None):
        self.type = "tool_use" if name else "text"
        self.name, self.input, self.text = name, inp or {}, text
        self.id = f"t{random.randrange(1 << 30):x}"


def sample_input(schema):
    """A plausible payload for a tool, built from its own schema."""
    out = {}
    for k, v in schema["input_schema"]["properties"].items():
        t = v.get("type", "string")
        out[k] = (5 if t == "integer" else
                  1.0 if t == "number" else
                  True if t == "boolean" else
                  ("notes.txt" if k == "path" else "MCP release date"))
    return out


def smoke(verbose=True):
    """Call every tool in every condition exactly as the loop would.

    This exists because the scripted dry run passed while six of the
    fifteen `muddy` tools raised TypeError on their first call -- the
    stand-in only ever asked for the three core tools, so it never
    touched the others. A harness check that only walks the happy path
    is not a harness check.
    """
    broken = []
    for cond in toolsets.CONDITIONS:
        schemas, reg = toolsets.build(cond)
        bad = []
        for s in schemas:
            if s["name"] == "done":
                continue
            fn = reg.get(s["name"])
            if fn is None:
                bad.append((s["name"], "missing from registry", ""))
                continue
            try:
                fn(**sample_input(s))
            except Exception as e:                       # noqa: BLE001
                bad.append((s["name"], type(e).__name__, str(e)[:70]))
        if verbose:
            print(f"  {cond:<6} {len(schemas)-1:>2} callable tools, "
                  f"{len(bad)} broken")
            for n, t, m in bad:
                print(f"      {n:<18} {t}: {m}")
        broken += bad
    return broken


def fake_ask(rng, schemas, condition):
    """A scripted stand-in so the harness can be checked without spending
    anything. It is NOT a simulation of the model and no number it
    produces may ever appear on camera.

    It deliberately wanders: detours through non-core tools, occasional
    step-cap overruns, occasional giving up. The first version only ever
    walked search-search-write-done, which is why it missed six broken
    tools.
    """
    names = [t["name"] for t in schemas if t["name"] != "done"]
    extras = [n for n in names if n not in ("search", "write_file")]
    st = fake_ask.state
    st["n"] += 1
    tin = 800 + 90 * len(schemas) + 140 * (st["n"] - 1)

    if extras and rng.random() < 0.30:              # wander off
        pick = rng.choice(extras)
        sch = next(t for t in schemas if t["name"] == pick)
        return FakeResponse([Block(pick, sample_input(sch))], tin, 60)
    if st["n"] > 9 and rng.random() < 0.4:          # give up with text
        return FakeResponse([Block(text="I cannot complete this.")], tin, 30)
    if not st["searched"]:
        st["searched"] = True
        return FakeResponse([Block("search", {"query": "when MCP released"})], tin, 70)
    if not st["searched2"]:
        st["searched2"] = True
        return FakeResponse([Block("search", {"query": "what changed since"})], tin, 70)
    if not st["wrote"]:
        st["wrote"] = True
        txt = ("Released 25 November 2024. Since then: donated to the "
               "Agentic AI Foundation; 2026-07-28 revision made it stateless.")
        if rng.random() < 0.25:
            txt = "Released 25 November 2024."
        return FakeResponse([Block("write_file", {"path": "notes.txt",
                                                  "content": txt})], tin, 90)
    if rng.random() < 0.15:                         # keep going past the cap
        return FakeResponse([Block("search", {"query": "one more check"})], tin, 60)
    return FakeResponse([Block("done", {"summary": "ok"})], tin, 40)


def run_once(condition, dry, rng):
    schemas, registry = toolsets.build(condition)

    # A stale notes.txt from the previous run would make the oracle lie.
    if tools.OUT_DIR.exists():
        for p in tools.OUT_DIR.glob("*.txt"):
            p.unlink()

    model.CALLS = model.TOKENS_IN = model.TOKENS_OUT = 0
    model.CALL_LOG.clear()
    if dry:
        fake_ask.state = {"n": 0, "searched": False, "searched2": False,
                          "wrote": False}

    messages = [{"role": "user", "content": TASK}]
    seq, errors, t0, stopped = [], [], time.time(), "cap"

    for step in range(1, MAX_STEPS + 1):
        if dry:
            r = fake_ask(rng, schemas, condition)
            model.CALLS += 1
            model.CALL_LOG.append((model.CALLS, r.usage.input_tokens,
                                   r.usage.output_tokens))
            model.TOKENS_IN += r.usage.input_tokens
            model.TOKENS_OUT += r.usage.output_tokens
        else:
            r = ask_with_retry(messages, schemas)
        messages.append({"role": "assistant", "content": r.content})

        calls = [b for b in r.content if b.type == "tool_use"]
        if not calls:
            stopped = "gave_up"
            break

        results, finished = [], False
        for call in calls:
            seq.append(call.name)
            if call.name == "done":
                stopped, finished = "done", True
                break
            fn = registry.get(call.name)
            if fn is None:
                out = f"No such tool: {call.name}"
                errors.append(f"{call.name}: not in registry")
            else:
                # A tool that raises must not take 30 minutes of runs with
                # it. The model is told what went wrong and carries on,
                # which is also what a real harness would do.
                try:
                    out = fn(**call.input)
                except Exception as e:               # noqa: BLE001
                    out = f"Tool error: {type(e).__name__}: {e}"
                    errors.append(f"{call.name}: {type(e).__name__}: {e}")
            results.append({"type": "tool_result", "tool_use_id": call.id,
                            "content": str(out)})
        if finished:
            break
        messages.append({"role": "user", "content": results})

    note = tools.OUT_DIR / "notes.txt"
    text = note.read_text() if note.exists() else ""
    has_rel, has_chg = bool(RELEASED.search(text)), bool(CHANGED.search(text))
    core = {"search", "write_file", "done"}

    return {
        "condition": condition,
        "stopped": stopped,
        "steps": len(model.CALL_LOG),
        "seq": seq,
        "call_one_in": model.CALL_LOG[0][1] if model.CALL_LOG else 0,
        "total_in": model.TOKENS_IN,
        "total_out": model.TOKENS_OUT,
        "seconds": round(time.time() - t0, 1),
        "wrote_note": bool(text),
        "has_release": has_rel,
        "has_change": has_chg,
        "correct": has_rel and has_chg,
        "off_core_calls": sum(1 for n in seq if n not in core),
        "note_chars": len(text),
        "errors": errors,
        # The task needs exactly two searches. Anything more is what a bad
        # tool choice costs you, which is the thing experiment 1 could not
        # see because every search tool returned the same corpus.
        "searches": sum(1 for n in seq if n in toolsets.SEARCH_TOOLS),
        "first_search": next((n for n in seq if n in toolsets.SEARCH_TOOLS), None),
        "search_seq": [n for n in seq if n in toolsets.SEARCH_TOOLS],
        "split": toolsets.SPLIT,
    }


def use_gzip_only():
    """Rebuild the client so the server never sends brotli.

    Some environments carry a brotli binding whose decoder signature does
    not match what the HTTP layer expects, and every response dies with
    `TypeError: process() takes no keyword arguments` wrapped in an
    APIConnectionError. Asking for gzip sidesteps the broken decoder
    without touching the environment. It is a workaround, not a fix --
    the real fix is in the note this prints."""
    import anthropic
    model.client = anthropic.Anthropic(
        default_headers={"Accept-Encoding": "gzip"})


def preflight():
    """One cheap call, before sixty expensive ones.

    A connection problem should cost two seconds, not the thirty minutes
    it takes to discover it half way through the muddy condition."""
    try:
        model.client.messages.create(
            model=model.MODEL, max_tokens=1,
            messages=[{"role": "user", "content": "hi"}])
        return True
    except Exception as e:                           # noqa: BLE001
        msg = f"{type(e).__name__}: {e}"
        print(f"\n  the API is not reachable from this interpreter")
        print(f"    {msg}")
        if "process()" in str(e) or "ConnectionError" in type(e).__name__:
            print("\n  If the underlying error mentions `process() takes no "
                  "keyword arguments`,")
            print("  that is a brotli decoder mismatch in this environment, "
                  "not your API key.")
            print("  In order of preference:")
            print("    1. run inside the repo's venv:  source .venv/bin/activate")
            print("    2. pip install --upgrade brotli brotlicffi")
            print("    3. re-run this with --gzip, which asks the server for")
            print("       gzip instead and leaves your environment alone")
        return False


def ask_with_retry(messages, schemas, tries=5):
    """Sixty runs is long enough to meet a rate limit or a 529. Losing the
    whole experiment to one of those would cost a day."""
    for i in range(tries):
        try:
            return model.ask(messages, tools=schemas, system=SYSTEM)
        except Exception as e:                       # noqa: BLE001
            if i == tries - 1:
                raise
            wait = 2 ** i + random.random()
            print(f"      {type(e).__name__}, retrying in {wait:.1f}s")
            time.sleep(wait)


# ----------------------------------------------------------- reporting --
def summarise(runs, n_per):
    by = {c: [r for r in runs if r["condition"] == c] for c in toolsets.CONDITIONS}
    print(f"\n  {len(runs)} runs, {n_per} per condition, "
          f"model {model.MODEL}, task needs {IDEAL_STEPS} steps\n")
    hdr = (f"  {'':<7}{'tools':>6}{'correct':>18}{'finished':>10}"
           f"{'call 1 in':>11}{'total in':>10}{'steps':>7}{'searches':>10}")
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for c in toolsets.CONDITIONS:
        rs = by[c]
        if not rs:
            continue
        n = len(rs)
        k = sum(r["correct"] for r in rs)
        lo, hi = wilson(k, n)
        fin = sum(r["stopped"] == "done" for r in rs)
        ntools = len(toolsets.build(c)[0])
        print(f"  {c:<7}{ntools:>6}"
              f"{f'{k}/{n}  {lo*100:.0f}-{hi*100:.0f}%':>18}"
              f"{f'{fin}/{n}':>10}"
              f"{med([r['call_one_in'] for r in rs]):>11,.0f}"
              f"{med([r['total_in'] for r in rs]):>10,.0f}"
              f"{med([r['steps'] for r in rs]):>7.1f}"
              f"{med([r['searches'] for r in rs]):>10.1f}")

    if toolsets.SPLIT:
        print("\n  Which search did it reach for first, and did that cost it?")
        for c in toolsets.CONDITIONS:
            rs = by[c]
            if not rs:
                continue
            firsts = collections.Counter(r["first_search"] for r in rs)
            extra = sum(1 for r in rs if r["searches"] > 2)
            print(f"    {c:<6} first pick: "
                  + "  ".join(f"{k}x{v}" for k, v in firsts.most_common())
                  + f"   |  {extra}/{len(rs)} runs needed more than two searches")

    print("\n  Is the difference real, or is it twenty coin flips?")
    for a, b in (("small", "real"), ("small", "muddy"), ("real", "muddy")):
        ra, rb = by[a], by[b]
        if not ra or not rb:
            continue
        ka, kb = sum(r["correct"] for r in ra), sum(r["correct"] for r in rb)
        p = fisher(ka, len(ra) - ka, kb, len(rb) - kb)
        verdict = ("a real difference" if p < 0.05 else
                   "NOT distinguishable at this sample size")
        print(f"    {a:>5} {ka}/{len(ra)}  vs  {b:<5} {kb}/{len(rb)}"
              f"    Fisher p = {p:.3f}   {verdict}")
    print("\n  A null result here is a finding, not a failed experiment.")
    print(f"  What {n_per} runs an arm can resolve, by Fisher:")
    for a, b in ((n_per, int(n_per*0.7)), (n_per, int(n_per*0.6)),
                 (int(n_per*0.8), int(n_per*0.5))):
        pv = fisher(a, n_per - a, b, n_per - b)
        mark = "detectable" if pv < 0.05 else "NOT detectable"
        print(f"    {a}/{n_per} vs {b}/{n_per}  ->  p = {pv:.3f}   {mark}")
    print("  A gap narrower than that comes back indistinguishable, and the")
    print("  script has to say so rather than round it up into a claim.")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    dry = "--dry-run" in sys.argv
    if "--split" in sys.argv:
        toolsets.SPLIT = True
        print("  SPLIT: each search tool has its own, narrower corpus")
    if "--gzip" in sys.argv:
        use_gzip_only()
        print("  asking the server for gzip (brotli decoder bypassed)")
    if "--smoke" in sys.argv:
        raise SystemExit(1 if smoke() else 0)
    n_per = int(args[0]) if args else 20
    if not dry and not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("  ANTHROPIC_API_KEY is not set")

    print("\n  checking every tool in every condition is callable:")
    broken = smoke()
    if broken:
        raise SystemExit(f"\n  {len(broken)} tools are broken. "
                         "Not running the experiment.\n")
    print()

    if not dry and not preflight():
        raise SystemExit(1)

    rng = random.Random(3)
    runs = []
    out = ROOT / "evidence"
    out.mkdir(exist_ok=True)
    tag = "split-" if toolsets.SPLIT else ""
    f = out / f"tools-{tag}{datetime.now():%Y%m%d-%H%M%S}.json"

    def save():
        f.write_text(json.dumps({"model": model.MODEL, "task": TASK,
                                 "n_per_condition": n_per,
                                 "split": toolsets.SPLIT,
                                 "complete": len(runs) == n_per * 3,
                                 "runs": runs}, indent=1))

    for c in toolsets.CONDITIONS:
        for i in range(n_per):
            r = run_once(c, dry, rng)
            runs.append(r)
            if not dry:
                save()            # a crash at run 55 must not cost runs 1-54
            flag = "ok " if r["correct"] else "BAD"
            err = f"  !! {r['errors'][0]}" if r["errors"] else ""
            print(f"  {c:<6} {i+1:>3}/{n_per}  {flag} "
                  f"{r['steps']:>2} steps  {r['total_in']:>7,} in  "
                  f"{'+'.join(r['seq'][:6])}{err}")

    summarise(runs, n_per)
    n_err = sum(1 for r in runs if r["errors"])
    if n_err:
        print(f"\n  {n_err} runs hit a tool error -- check `errors` in the JSON")
    if dry:
        print("\n  DRY RUN -- these numbers are scripted and mean nothing.\n")
        return
    print(f"\n  evidence -> {f.relative_to(ROOT)}\n")


if __name__ == "__main__":
    main()
