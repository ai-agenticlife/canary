#!/bin/bash
# Cold open premise check: on the EASY task, do workflow.py and
# agent.py write the SAME notes.txt?
#
#   bash check_match.sh [N]        (default 5)
#
# The cold open's narration says "same request going in, same answer
# coming out." If this script says MATCH every time, that line is
# true on camera. If it says DIFFER, don't shoot yet.

set -u
cd "$(dirname "$0")"
N="${1:-5}"
PY="$(pwd)/.venv/bin/python"
NOTES="$(pwd)/out/notes.txt"
LOG="$(pwd)/match-log.txt"
: > "$LOG"

say() { echo "$@" | tee -a "$LOG"; }
say "NOTES MATCH CHECK — $N rounds — $(date)"
say ""

MATCH=0
for i in $(seq 1 "$N"); do
  rm -f "$NOTES"
  ( cd canary && "$PY" workflow.py >/dev/null 2>&1 )
  A=$(cat "$NOTES" 2>/dev/null)

  rm -f "$NOTES"
  ( cd canary && "$PY" agent.py >/dev/null 2>&1 )
  B=$(cat "$NOTES" 2>/dev/null)

  if [ "$A" = "$B" ]; then
    say "round $i: MATCH   (${#A} chars)"
    MATCH=$((MATCH+1))
  else
    say "round $i: DIFFER  (workflow ${#A} chars, agent ${#B} chars)"
    say "  ── workflow ──"
    echo "$A" | sed 's/^/  /' | tee -a "$LOG"
    say "  ── agent ──"
    echo "$B" | sed 's/^/  /' | tee -a "$LOG"
    say ""
  fi
done

say ""
say "════════════════════════════════════════"
say "$MATCH of $N rounds matched."
if [ "$MATCH" -eq "$N" ]; then
  say "GOOD — the cold open premise holds. Shoot it."
else
  say "NOT READY — send match-log.txt to Claude before shooting."
fi
