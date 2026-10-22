#!/bin/bash
# Canary v0 — live API smoke test.
# Creates its own isolated virtualenv so a tangled Anaconda base
# environment can't break it. Writes canary-test-log.txt.
#
#   bash run_canary_test.sh
#
# Never prints your API key.

set -u
cd "$(dirname "$0")"
LOG="$(pwd)/canary-test-log.txt"
: > "$LOG"

say() { echo "$@" | tee -a "$LOG"; }

say "CANARY v0 LIVE TEST — $(date)"
say ""

# ── preflight ───────────────────────────────────────────────────
if ! command -v python3 >/dev/null; then
  say "!! python3 not found."; exit 1
fi
say "python3: $(python3 --version 2>&1)  [$(command -v python3)]"

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  say ""
  say "!! ANTHROPIC_API_KEY is not set. Run this, then re-run the script:"
  say "       export ANTHROPIC_API_KEY=sk-ant-...your-key..."
  exit 1
fi
say "api key: set (${#ANTHROPIC_API_KEY} chars)"
say "model:   ${CANARY_MODEL:-claude-sonnet-4-5 (default)}"

# ── isolated environment ────────────────────────────────────────
# Anaconda's base env has incompatible brotli/httpx/h11 versions that
# make every API response fail to decompress. A venv sidesteps it.
if [ ! -d .venv ]; then
  say ""
  say "creating an isolated environment (.venv) — one-time, ~30s..."
  python3 -m venv .venv 2>&1 | tee -a "$LOG"
fi
PY="$(pwd)/.venv/bin/python"
if [ ! -x "$PY" ]; then
  say "!! could not create .venv — is the 'venv' module available?"; exit 1
fi

"$PY" -m pip install --quiet --upgrade pip >/dev/null 2>&1
if ! "$PY" -c "import anthropic" 2>/dev/null; then
  say "installing the anthropic package into .venv..."
  "$PY" -m pip install --quiet anthropic 2>&1 | tail -5 | tee -a "$LOG"
fi
say "$("$PY" -c "import anthropic,httpx; print('anthropic',anthropic.__version__,'| httpx',httpx.__version__)" 2>&1)"

# ── connectivity probe before the real runs ─────────────────────
say ""
say "probing the API..."
PROBE=$("$PY" - <<'PY' 2>&1
import os, anthropic
try:
    c = anthropic.Anthropic()
    r = c.messages.create(
        model=os.environ.get("CANARY_MODEL", "claude-sonnet-4-5"),
        max_tokens=16,
        messages=[{"role": "user", "content": "Reply with the single word: ok"}],
    )
    print("PROBE OK ->", "".join(b.text for b in r.content if b.type == "text").strip())
except Exception as e:
    print(f"PROBE FAILED -> {type(e).__name__}: {e}")
PY
)
say "$PROBE"
case "$PROBE" in
  *"PROBE OK"*) ;;
  *) say ""; say "Stopping — the probe failed. Send this log to Claude."; exit 1 ;;
esac

run() {
  say ""
  say "════════════════════════════════════════════════════════════"
  say "$1"
  say "════════════════════════════════════════════════════════════"
  shift
  ( cd canary && "$PY" "$@" ) 2>&1 | tee -a "$LOG"
}

EASY="Find out when the Model Context Protocol was released and save it to notes.txt."
HARD="Find out when MCP was released. If it is more than a year old, also find out what changed since then. Save both to notes.txt."

run "1/5  WORKFLOW — easy task (should succeed)"                          workflow.py "$EASY"
run "2/5  AGENT — easy task (should match the workflow)"                  agent.py    "$EASY"
run "3/5  WORKFLOW — conditional task (SHOULD BE INCOMPLETE, not crash)"  workflow.py "$HARD"
run "4/5  AGENT — conditional task (should search twice)"                 agent.py    "$HARD"
run "5/5  AGENT — same task again (should take a different route)"        agent.py    "$HARD"

say ""
say "════════════════════════════════════════════════════════════"
say "DONE — send canary-test-log.txt to Claude"
say "════════════════════════════════════════════════════════════"
echo
echo "Log written to: $LOG"
