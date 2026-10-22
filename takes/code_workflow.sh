source "$(dirname "$0")/_lib.sh"; setup
type_cmd 'sed -n "/^def main/,/^if __name__/p" workflow.py'
sed -n '/^def main/,/^if __name__/p' workflow.py
sleep 10
