source "$(dirname "$0")/_lib.sh"; setup
type_cmd 'sed -n "/^def main/,/^def _short/p" agent.py'
sed -n '/^def main/,/^def _short/p' agent.py
sleep 10
