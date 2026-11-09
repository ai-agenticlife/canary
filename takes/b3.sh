source "$(dirname "$0")/_lib.sh"
# Block 3: experiment one, read back out of its own evidence file.
# Nothing is re-run and nothing is asked of the model, so the numbers on
# screen are the numbers from the run named at the top of the output.
type_cmd 'python show.py evidence/tools-20261030-160427.json'
python show.py evidence/tools-20261030-160427.json
sleep 35.5
type_cmd 'python show.py evidence/tools-20261030-160427.json --bill'
python show.py evidence/tools-20261030-160427.json --bill
sleep 22
