#!/usr/bin/env python3
"""Print what a tool-count run actually produced, from its evidence file.

    show.py evidence/tools-20261030-160427.json [--paths] [--worst]

Reads only the JSON the experiment wrote. It re-runs nothing and asks the
model nothing, so the numbers on screen are the numbers from the run named
at the top of the output -- which, after episode 2, is the whole point.

Output is kept inside 72 columns so it is legible when it is on screen.
"""
import json, sys
from collections import Counter
from pathlib import Path

W = 72
CONDS = ("small", "real", "muddy")


def med(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    f = Path(args[0])
    d = json.loads(f.read_text())
    runs = d["runs"]

    print()
    print(f"  {f.name}")
    print(f"  {d['model']}   {len(runs)} runs   "
          f"{d['n_per_condition']} per condition")
    print()
    print("  condition    correct    steps      call one    whole run")
    print()
    for c in CONDS:
        r = [x for x in runs if x["condition"] == c]
        if not r:
            continue
        ok = sum(x["correct"] for x in r)
        st = [x["steps"] for x in r]
        print(f"  {c:<11}  {ok:>2}/{len(r):<2}     "
              f"{med(st):>4.0f}       "
              f"{med([x['call_one_in'] for x in r]):>7,.0f}    "
              f"{med([x['total_in'] for x in r]):>9,.0f}")
    print()

    # the path every run took, and whether they all took the same one
    for c in CONDS:
        r = [x for x in runs if x["condition"] == c]
        if not r:
            continue
        paths = Counter(" ".join(x["seq"]) for x in r)
        top, n = paths.most_common(1)[0]
        if len(paths) == 1:
            print(f"  {c:<6}  all {len(r)} runs took the same path:")
        else:
            print(f"  {c:<6}  {n} of {len(r)} runs took:")
        for line in wrap(top, W - 12):
            print(f"            {line}")
        if len(paths) > 1:
            print(f"            ... and {len(paths)-1} other path(s)")
    print()

    if "--bill" in flags:
        # What the twelve unused tools cost, from the same file. The per-tool
        # figure is the marginal cost of the tools that were ADDED, not the
        # average over all fifteen -- those are different numbers and only
        # one of them answers "what does one more tool cost me".
        s = [x for x in runs if x["condition"] == "small"]
        r = [x for x in runs if x["condition"] == "real"]
        n_added = 12
        for name, kk in (("call one", "call_one_in"), ("whole run", "total_in")):
            a, b = med([x[kk] for x in s]), med([x[kk] for x in r])
            print(f"  {name:<12}{a:>8,.0f}  ->{b:>8,.0f}"
                  f"{b-a:>+9,.0f}{(b/a-1)*100:>8.0f}%")
        a = med([x["call_one_in"] for x in s])
        b = med([x["call_one_in"] for x in r])
        print()
        print(f"  {(b-a)/n_added:.0f} tokens for each of the {n_added} tools "
              f"that were added,")
        print(f"  on every call, and the run never called one of them.")
        print()

    if len(args) > 1:
        # Side by side with an earlier run. The narration says the median
        # "did not move at all" between the two experiments; the steps did
        # not, and the token median moved by five. Putting both figures up
        # is cheaper than being caught rounding one into the other.
        e = json.loads(Path(args[1]).read_text())
        a = [x for x in e["runs"] if x["condition"] == "muddy"]
        b = [x for x in runs if x["condition"] == "muddy"]
        ma, mb = med([x["total_in"] for x in a]), med([x["total_in"] for x in b])
        print(f"  median muddy run        {Path(args[1]).name[:14]:>16}"
              f"{Path(args[0]).name[:14]:>16}")
        print()
        print(f"  {'steps':<22}{med([x['steps'] for x in a]):>16.0f}"
              f"{med([x['steps'] for x in b]):>16.0f}")
        print(f"  {'tokens in':<22}{ma:>16,.0f}{mb:>16,.0f}")
        print(f"  {'runs past 2x median':<22}"
              f"{sum(x['total_in'] > 2*ma for x in a):>16}"
              f"{sum(x['total_in'] > 2*mb for x in b):>16}")
        print()

    if "--worst" in flags:
        out = [x for x in runs if x["condition"] == "muddy"]
        out.sort(key=lambda x: -x["steps"])
        base = med([x["total_in"] for x in out])
        print("  the tail:")
        for x in out[:3]:
            if x["steps"] <= med([y["steps"] for y in out]):
                break
            print(f"    {x['steps']:>2} steps   {x['total_in']:>7,} tokens   "
                  f"{x['total_in']/base:.1f}x the median   "
                  f"correct: {'yes' if x['correct'] else 'NO'}")
            for line in wrap(" ".join(x["seq"]), W - 8):
                print(f"        {line}")
        print()


def wrap(s, w):
    out, cur = [], ""
    for word in s.split():
        if len(cur) + len(word) + 1 > w:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        out.append(cur)
    return out


if __name__ == "__main__":
    main()
