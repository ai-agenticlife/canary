source "$(dirname "$0")/_lib.sh"; setup
type_cmd 'python agent.py "$HARD"'
python agent.py "$HARD"
sleep 1
type_cmd 'cat ../out/notes.txt'
cat ../out/notes.txt
echo
sleep 8
