#!/bin/bash
# Run the agent until it produces a SHORT run (one search instead of
# two) and show exactly what that run wrote to notes.txt.
#
#   bash catch_failure.sh [max_attempts]     (default 15)
#
# We need to know whether a one-search run admits the gap or just
# quietly writes half the answer.

set -u
cd "$(dirname "$0")"
MAX="${1:-15}"
LOG="$(pwd)/failure-catch-log.txt"
: > "$LOG"
PY="$(pwd)/.venv/bin/python"
NOTES="$(pwd)/out/notes.txt"

HARD="Find out when MCP was released. If it is more than a year old, also find out what changed since then. Save both to notes.txt."

say() { echo "$@" | tee -a "$LOG"; }
say "CATCHING A ONE-SEARCH RUN — $(date)"
say ""

GOOD_SHOWN=0
for i in $(seq 1 "$MAX"); do
  rm -f "$NOTES"
  OUT=$( cd canary && "$PY" agent.py "$HARD" 2>&1 )
  NSEARCH=$(echo "$OUT" | grep -c "search(query=")
  STEPS=$(echo "$OUT" | grep -c '^  \[')
  say "attempt $i: $NSEARCH search(es), $STEPS steps"

  if [ "$NSEARCH" -ge 2 ] && [ "$GOOD_SHOWN" -eq 0 ]; then
    GOOD_SHOWN=1
    say ""
    say "──────── A CORRECT RUN ($NSEARCH searches) ────────"
    echo "$OUT" | tee -a "$LOG"
    say "──────── notes.txt it wrote ────────"
    cat "$NOTES" 2>/dev/null | tee -a "$LOG"
    say "────────────────────────────────────"
    say ""
  fi

  if [ "$NSEARCH" -eq 1 ]; then
    say ""
    say "★★★ CAUGHT A ONE-SEARCH RUN on attempt $i ★★★"
    echo "$OUT" | tee -a "$LOG"
    say ""
    say "──────── notes.txt it wrote ────────"
    cat "$NOTES" 2>/dev/null | tee -a "$LOG"
    say "────────────────────────────────────"
    say ""
    say "Does it admit the gap, or state the date as the whole answer?"
    say "DONE — send failure-catch-log.txt to Claude"
    exit 0
  fi
done

say ""
say "No one-search run in $MAX attempts. Re-run to try again."
