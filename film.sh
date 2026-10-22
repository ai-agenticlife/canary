# Set up a terminal pane for recording. SOURCE this, don't run it —
# it changes the shell, so it has to happen in your shell.
#
#   source ~/Documents/AgenticLife_YouTube/canary-v0/film.sh
#
# Or add the alias from RECORDING.md and just type:  film

CANARY_ROOT="$HOME/Documents/AgenticLife_YouTube/canary-v0"

cd "$CANARY_ROOT/canary" 2>/dev/null || {
  echo "!! can't find $CANARY_ROOT/canary"
  return 1 2>/dev/null || exit 1
}

export VIRTUAL_ENV_DISABLE_PROMPT=1
source "$CANARY_ROOT/.venv/bin/activate" 2>/dev/null || {
  echo "!! no .venv — run:  bash $CANARY_ROOT/run_canary_test.sh"
  return 1 2>/dev/null || exit 1
}

PROMPT='%F{cyan}❯ %f'

# ── readiness report ────────────────────────────────────────────
echo
PY_PATH="$(which python)"
case "$PY_PATH" in
  *"canary-v0/.venv"*) echo "  python   OK    $PY_PATH" ;;
  *)                   echo "  python   WRONG $PY_PATH  <- not the venv" ;;
esac

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "  api key  OK    set (${#ANTHROPIC_API_KEY} chars)"
else
  echo "  api key  MISSING — add it to ~/.zshrc, then open a NEW window"
fi

echo "  model    ${CANARY_MODEL:-claude-sonnet-4-5 (default)}"

# 78-84 columns per pane. Below 78 and long lines wrap; above 84 the
# glyphs are too small to read on a phone. This is the single setting
# most likely to ruin a take, so it is a hard pass/fail.
COLS=$(tput cols)
if [ "$COLS" -lt 78 ]; then
  echo "  width    TOO NARROW  $COLS columns — need 78-84."
  echo "                       Cmd and minus until it reads 78-84, then re-run film."
elif [ "$COLS" -gt 84 ]; then
  echo "  width    TOO WIDE    $COLS columns — need 78-84. Text will be"
  echo "                       unreadable on a phone."
  echo "                       Cmd and plus until it reads 78-84, then re-run film."
else
  echo "  width    OK          $COLS columns"
fi

echo
echo "  Ready. Cmd+K to clear, then type your command (don't press Enter yet)."
echo
