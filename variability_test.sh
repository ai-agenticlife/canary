#!/bin/bash
# How much does the agent's route actually vary?
# Runs the same task N times and prints each run's step signature.
#
#   bash variability_test.sh [N]        (default 10)

set -u
cd "$(dirname "$0")"
N="${1:-10}"
LOG="$(pwd)/variability-log.txt"
: > "$LOG"
PY="$(pwd)/.venv/bin/python"

HARD="Find out when MCP was released. If it is more than a year old, also find out what changed since then. Save both to notes.txt."

say() { echo "$@" | tee -a "$LOG"; }
say "AGENT VARIABILITY — $N runs of the same command — $(date)"
say ""

for i in $(seq 1 "$N"); do
  OUT=$( cd canary && "$PY" agent.py "$HARD" 2>&1 )
  SIG=$(echo "$OUT" | grep -oE '\] [a-z_]+\(' | sed 's/[](]//g;s/ //g' | paste -sd'>' -)
  STEPS=$(echo "$OUT" | grep -c '^  \[')
  CALLS=$(echo "$OUT" | grep -oE 'AGENT: [0-9]+ model calls' | grep -oE '[0-9]+')
  TOK=$(echo "$OUT"   | grep -oE '\| [0-9]+ tokens' | grep -oE '[0-9]+')
  Q=$(echo "$OUT" | grep -oE "search\(query='[^']*" | sed "s/search(query='//" | paste -sd' | ' -)
  say "run $i:  $STEPS steps, $CALLS calls, $TOK tokens"
  say "        $SIG"
  say "        queries: $Q"
  say ""
done

say "════════════════════════════════════════════════"
say "distinct step signatures:"
grep -E '^        [a-z_]+>' "$LOG" | sed 's/^ *//' | sort | uniq -c | sort -rn | tee -a "$LOG"
say ""
say "distinct query sets:"
grep '^        queries:' "$LOG" | sed 's/^ *queries: //' | sort | uniq -c | sort -rn | tee -a "$LOG"
echo
echo "Log written to: $LOG"
