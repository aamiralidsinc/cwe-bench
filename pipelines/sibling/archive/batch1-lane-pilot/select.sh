#!/bin/bash
# select.sh <deepseek|mimo>
# The driver model scores the candidate pool and picks its own top 50. Fully model-driven
# selection. Writes build/pipeline/selection_<driver>.json (array of {entry_id,score,reason}).
set -uo pipefail
D=${1:?usage: select.sh <deepseek|mimo>}
R="$HOME/cwe-bench"; cd "$R" || exit 1
mkdir -p build/pipeline
POOL=build/pipeline/pool.jsonl
[ -s "$POOL" ] || { echo "no pool ($POOL); run make_pool.py" >&2; exit 2; }
# The combined prompt (rubric + 150-line pool) is ~240KB, over Linux's 128KB single-arg
# limit, so it must go to claude via STDIN, not as an argument.
PF=build/pipeline/select_prompt_$D.txt
{ cat builder/SELECT-PROMPT.md; echo; cat "$POOL"; } > "$PF"
RAW=build/pipeline/selection_$D.raw.json
OUT=build/pipeline/selection_$D.json
date -u +%FT%TZ > build/pipeline/select_${D}_start.txt
# drive.sh sets MODEL and the provider env; the inner bash reads MODEL at runtime and
# pipes the prompt file into claude's stdin.
timeout 2400 ./drive.sh "$D" bash -c \
  'cat "$1" | "$HOME/.local/bin/claude" -p --model "$MODEL" --output-format json --max-turns 3' \
  _ "$PF" > "$RAW" 2> build/pipeline/select_$D.err
# Pull the model text, then the JSON array inside it.
python3 - "$RAW" "$OUT" <<'PY'
import json, re, sys
raw, out = sys.argv[1], sys.argv[2]
d = json.load(open(raw))
txt = d.get("result") or ""
m = re.search(r"\[\s*{.*}\s*\]", txt, re.S)
if not m:
    print("NO JSON ARRAY in model output; see", raw); sys.exit(1)
arr = json.loads(m.group(0))
# keep only well-formed rows with an entry_id
arr = [x for x in arr if isinstance(x, dict) and x.get("entry_id")]
json.dump(arr, open(out, "w"), indent=1)
print(f"selected {len(arr)} candidates -> {out}")
PY
