source "$(dirname "$0")/_lib.sh"
# Block 6, first half: the hole in experiment one and the fix, both of
# which are written as a comment above SPLIT. The reasoning is in the
# repo, so the take reads it from the repo.
type_cmd "sed -n '/^# Experiment 1 could not/,/removal window/p' canary/toolsets.py"
sed -n '/^# Experiment 1 could not/,/removal window/p' canary/toolsets.py
sleep 46
