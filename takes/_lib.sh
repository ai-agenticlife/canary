# Shared helpers for the recorded takes.
# The command is typed out character by character so the cast looks like a
# live session. The command and its output are real; only the keystroke
# timing is synthetic.

PROMPT=$'\033[36m\xe2\x9d\xaf\033[0m '

type_cmd() {
  printf '%s' "$PROMPT"
  local s="$1" i
  for ((i = 0; i < ${#s}; i++)); do
    printf '%s' "${s:$i:1}"
    sleep 0.05
  done
  printf '\n'
  sleep 0.35
}

setup() {
  cd "$HOME/Documents/AgenticLife_YouTube/canary-v0/canary" || exit 1
  export VIRTUAL_ENV_DISABLE_PROMPT=1
  source ../.venv/bin/activate || exit 1
}

HARD="Find out when MCP was released. If it is more than a year old, also find out what changed since then. Save both to notes.txt."
