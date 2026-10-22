source "$(dirname "$0")/_lib.sh"; setup
type_cmd 'python workflow.py "$HARD"'
python workflow.py "$HARD"
sleep 1
type_cmd 'cat ../out/notes.txt'
cat ../out/notes.txt
echo
sleep 10
