source "$(dirname "$0")/_lib.sh"
# Block 6, second half: experiment two beside experiment one, and the tail.
CMD='python show.py evidence/tools-split-20261107-112239.json \'
type_cmd "$CMD"
type_cmd '    evidence/tools-20261030-160427.json --worst'
python show.py evidence/tools-split-20261107-112239.json \
    evidence/tools-20261030-160427.json --worst
sleep 42
