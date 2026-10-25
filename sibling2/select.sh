#!/bin/bash
# sibling2/select.sh <deepseek|mimo>
# pipeline/select.sh unchanged except that every path is under sibling2/out/pipeline/, so batch-1's
# build/pipeline/selection_*.json is never overwritten. The driver model scores the sibling2 pool and
# picks its own top 50 (count set by builder/SELECT-PROMPT.md). Writes selection_<driver>.json.
set -uo pipefail
D=${1:?usage: sibling2/select.sh <deepseek|mimo>}
R="$HOME/cwe-bench"; cd "$R" || exit 1
P=sibling2/out/pipeline
mkdir -p "$P"
POOL=$P/pool.jsonl
[ -s "$POOL" ] || { echo "no pool ($POOL); run sibling2/lane.py pool" >&2; exit 2; }
# rubric + pool goes to claude via STDIN (over the 128KB single-argument limit)
PF=$P/select_prompt_$D.txt
{ cat builder/SELECT-PROMPT.md; echo; cat "$POOL"; } > "$PF"
RAW=$P/selection_$D.raw.json
OUT=$P/selection_$D.json
date -u +%FT%TZ > $P/select_${D}_start.txt
timeout 2400 ./drive.sh "$D" bash -c \
  'cat "$1" | "$HOME/.local/bin/claude" -p --model "$MODEL" --output-format json --max-turns 3' \
  _ "$PF" > "$RAW" 2> $P/select_$D.err
python3 - "$RAW" "$OUT" <<'PY'
import json, re, sys
raw, out = sys.argv[1], sys.argv[2]
d = json.load(open(raw))
txt = d.get("result") or ""
m = re.search(r"\[\s*{.*}\s*\]", txt, re.S)
if not m:
    print("NO JSON ARRAY in model output; see", raw); sys.exit(1)
arr = [x for x in json.loads(m.group(0)) if isinstance(x, dict) and x.get("entry_id")]
json.dump(arr, open(out, "w"), indent=1)
print(f"selected {len(arr)} candidates -> {out}")
PY
