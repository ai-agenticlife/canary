#!/bin/bash
# Record every Canary shot for episode 1 as an asciinema cast.
#
#   bash record_takes.sh            # all nine
#   bash record_takes.sh easy_agent # just one, to retry it
#
# Nothing is typed by hand and nothing depends on your window size: each
# take runs non-interactively at a fixed terminal size. If a take comes
# out wrong, re-run that one by name -- there is no such thing as a
# "retake" any more, only a re-record and a re-render.
#
# Your API key is never printed. The casts contain program output only.

set -u
ROOT="$HOME/Documents/AgenticLife_YouTube/canary-v0"
OUT="$HOME/Documents/AgenticLife_YouTube/01 The Line/Canary"
mkdir -p "$OUT"

# name:COLSxROWS  -- code shots need the height, run shots don't
TAKES=(
  "repo:80x24"
  "code_workflow:84x40"
  "code_agent:84x40"
  "easy_workflow:80x24"
  "easy_agent:80x24"
  "hard_workflow:80x28"
  "hard_agent:80x28"
  "hard_agent2:80x24"
  "cliffhanger:80x30"
)

# Some takes are only usable if the program behaved a particular way.
# The agent picks its own route, so "record it again" is a real outcome,
# not an error -- about 1 run in 14 does one search instead of two and is
# useless for a shot whose narration says it searches twice.
VERIFY_WHY=""
verify() {
  local name="$1" f="$2" n
  case "$name" in
    hard_agent|hard_agent2)
      n=$(grep -o 'search(query=' "$f" | wc -l | tr -d ' ')
      if [ "$n" -lt 2 ]; then
        VERIFY_WHY="only $n search, needs 2 - rerun: bash record_takes.sh $name"
        return 1
      fi ;;
    easy_workflow|easy_agent)
      grep -q '25 November 2024' "$f" || {
        VERIFY_WHY="the release date is not in the output"; return 1; } ;;
    hard_workflow)
      grep -qi 'no information available\|do not contain\|only contain' "$f" || {
        VERIFY_WHY="the workflow did not state its own gap this run"; return 1; } ;;
    cliffhanger)
      grep -q '\[1[3-9]\]\|\[2[0-9]\]' "$f" || {
        VERIFY_WHY="never climbed past step 12"; return 1; } ;;
  esac
  return 0
}

want="${1:-}"
fail=0
for entry in "${TAKES[@]}"; do
  name="${entry%%:*}"; size="${entry##*:}"
  [ -n "$want" ] && [ "$want" != "$name" ] && continue
  printf '  %-16s %-8s ' "$name" "$size"
  if asciinema rec --overwrite -q \
       --window-size "$size" \
       --idle-time-limit 3 \
       --title "Canary: $name" \
       -c "cd '$ROOT' && bash takes/$name.sh" \
       "$OUT/$name.cast" >/dev/null 2>&1; then
    bytes=$(wc -c < "$OUT/$name.cast" | tr -d ' ')
    events=$(( $(wc -l < "$OUT/$name.cast") - 1 ))
    # Judge by size, not event count: `ls` legitimately produces ~5
    # events because its whole output arrives in one write.
    if [ "$bytes" -lt 400 ]; then
      echo "SUSPICIOUS - only ${bytes} bytes, probably failed"; fail=1
    elif ! verify "$name" "$OUT/$name.cast"; then
      echo "WRONG RUN - $VERIFY_WHY"; fail=1
    else
      echo "ok  ${events} events, ${bytes} bytes"
    fi
  else
    echo "FAILED"; fail=1
  fi
done

echo
if [ "$fail" -eq 0 ]; then
  echo "All takes recorded. Tell Claude."
else
  echo "Something failed above. Send Claude this output."
fi
