source "$(dirname "$0")/_lib.sh"
# Block 2. The two claims the episode separates are already written at the
# top of toolsets.py, so the take opens on the file's own reasoning rather
# than on an empty prompt -- which also means the frame is full from the
# first frame instead of holding on a command being typed.
type_cmd 'head -24 canary/toolsets.py'
head -24 canary/toolsets.py
sleep 17.5
type_cmd 'python canary/toolsets.py'
python canary/toolsets.py
sleep 25.8
type_cmd "sed -n '/^_MUDDY_SEARCH/,/^]/p' canary/toolsets.py"
sed -n '/^_MUDDY_SEARCH/,/^]/p' canary/toolsets.py
sleep 16
type_cmd "sed -n '/^def calculate/,/^def word_count/p' canary/toolsets.py"
sed -n '/^def calculate/,/^def word_count/p' canary/toolsets.py
sleep 7
