source "$(dirname "$0")/_lib.sh"; setup
# "Impossible" is not the same as "unanswerable". Asked to predict Bitcoin in
# 2035 the model correctly says it can't and stops -- sensible, and useless
# for this shot. What makes a loop run away is a task that is always ALMOST
# done: a verification condition it can keep working towards and never close.
IMPOSSIBLE="Find every change made to MCP since its release. Before you record any change, verify it with a separate, differently worded search. Do not call done until every change has been confirmed by at least three independent searches."
type_cmd 'CANARY_MAX_STEPS=200 python agent.py "$IMPOSSIBLE"'
# macOS has no `timeout`. Run it in the background and stop it ourselves.
CANARY_MAX_STEPS=200 python -u agent.py "$IMPOSSIBLE" &
pid=$!
for _ in $(seq 1 50); do
  kill -0 "$pid" 2>/dev/null || break
  sleep 1
done
kill "$pid" 2>/dev/null
wait "$pid" 2>/dev/null
