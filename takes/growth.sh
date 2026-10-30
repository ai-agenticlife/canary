source "$(dirname "$0")/_lib.sh"; setup
# One long run with the per-call token columns visible. Episode 2 uses
# this cast three times: the early climb in block 3, the later calls in
# block 6, and the final totals in block 7.
TASK="Find every change made to MCP since its release. Before you record any change, verify it with a separate, differently worded search. Do not call done until every change has been confirmed by at least three independent searches."
type_cmd 'CANARY_MAX_STEPS=25 python agent.py "$TASK"'
CANARY_MAX_STEPS=25 python -u agent.py "$TASK"
sleep 8
