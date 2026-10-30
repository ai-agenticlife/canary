#!/usr/bin/env python3
"""Does the loop's cost grow with the number of steps, or faster?

Episode 2 claims it grows faster. This is what has to be true before
that claim is allowed on camera.

Runs the agent on a task it cannot finish, records the input tokens for
every call, and fits both a straight line and a quadratic. Whichever
explains the data better, wins -- including if that is the straight line.

    python3 measure_growth.py [max_steps]        (default 25)
"""
import os, subprocess, sys, json, re
from pathlib import Path

ROOT = Path(__file__).parent
STEPS = int(sys.argv[1]) if len(sys.argv) > 1 else 25

TASK = ("Find every change made to MCP since its release. Before you record "
        "any change, verify it with a separate, differently worded search. "
        "Do not call done until every change has been confirmed by at least "
        "three independent searches.")

CODE = f'''
import sys, json
sys.path.insert(0, {str(ROOT / "canary")!r})
import model, tools
TASK = {TASK!r}
SYSTEM = (f"Today is {{tools.TODAY}}. You are a research assistant with tools. "
          "Work step by step. Call done() when the task is fully complete.")
msgs = [{{"role": "user", "content": TASK}}]
toolset = [tools.SEARCH_TOOL, tools.WRITE_TOOL, tools.DONE_TOOL]
for step in range(1, {STEPS} + 1):
    r = model.ask(msgs, tools=toolset, system=SYSTEM)
    msgs.append({{"role": "assistant", "content": r.content}})
    calls = [b for b in r.content if b.type == "tool_use"]
    if not calls:
        break
    out = []
    done = False
    for c in calls:
        if c.name == "done":
            done = True; break
        out.append({{"type": "tool_result", "tool_use_id": c.id,
                    "content": tools.REGISTRY[c.name](**c.input)}})
    if done:
        break
    msgs.append({{"role": "user", "content": out}})
print("@@@" + json.dumps(model.CALL_LOG))
'''

py = ROOT / ".venv" / "bin" / "python"
res = subprocess.run([str(py), "-c", CODE], capture_output=True, text=True,
                     cwd=ROOT / "canary")
m = re.search(r"@@@(\[.*\])", res.stdout)
if not m:
    print(res.stdout[-2000:]); print(res.stderr[-2000:])
    sys.exit("no data -- is ANTHROPIC_API_KEY set?")
log = json.loads(m.group(1))

print(f"\nTOKEN GROWTH -- {len(log)} model calls\n")
print(f"  {'call':>4} {'input':>9} {'output':>8} {'cumulative in':>14}")
cum = 0
for n, i, o in log:
    cum += i
    print(f"  {n:>4} {i:>9,} {o:>8,} {cum:>14,}")

xs = [n for n, _, _ in log]
ys = [i for _, i, _ in log]
N = len(xs)

def fit(deg):
    # plain least squares, no numpy needed
    import itertools
    A = [[x ** d for d in range(deg + 1)] for x in xs]
    AT = list(zip(*A))
    ATA = [[sum(a * b for a, b in zip(r, c)) for c in AT] for r in AT]
    ATy = [sum(a * y for a, y in zip(r, ys)) for r in AT]
    n = deg + 1
    for i in range(n):                       # gaussian elimination
        p = max(range(i, n), key=lambda r: abs(ATA[r][i]))
        ATA[i], ATA[p] = ATA[p], ATA[i]; ATy[i], ATy[p] = ATy[p], ATy[i]
        for r in range(i + 1, n):
            f = ATA[r][i] / ATA[i][i]
            for c in range(i, n): ATA[r][c] -= f * ATA[i][c]
            ATy[r] -= f * ATy[i]
    coef = [0.0] * n
    for i in reversed(range(n)):
        coef[i] = (ATy[i] - sum(ATA[i][c] * coef[c] for c in range(i + 1, n))) / ATA[i][i]
    pred = [sum(c * x ** d for d, c in enumerate(coef)) for x in xs]
    ybar = sum(ys) / N
    ss_res = sum((y - p) ** 2 for y, p in zip(ys, pred))
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    return coef, 1 - ss_res / ss_tot if ss_tot else 0.0

lin, r2_lin = fit(1)
quad, r2_quad = fit(2)
print(f"\n  straight line   R^2 = {r2_lin:.4f}   slope {lin[1]:,.0f} tokens/call")
print(f"  quadratic       R^2 = {r2_quad:.4f}   x^2 term {quad[2]:,.1f}")
print(f"\n  first call {ys[0]:,} in  ->  last call {ys[-1]:,} in   ({ys[-1]/ys[0]:.1f}x)")
print(f"  total input tokens across the run: {sum(ys):,}")
if abs(r2_quad - r2_lin) < 0.01:
    print("\n  VERDICT: a straight line explains it as well as a curve.")
    print("  Say 'grows every turn', NOT 'grows quadratically'.")
elif r2_quad > r2_lin:
    print("\n  VERDICT: the curve fits better than the line.")
else:
    print("\n  VERDICT: linear. Do not claim acceleration.")
