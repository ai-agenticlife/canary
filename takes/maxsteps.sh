source "$(dirname "$0")/_lib.sh"; setup
# Line 23. The narration names it, so the line numbers have to be real.
type_cmd 'awk "NR>=18 && NR<=28" agent.py'
awk 'NR>=18 && NR<=28 {printf "%3d  %s\n", NR, $0}' agent.py
sleep 10
