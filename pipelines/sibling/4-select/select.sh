#!/bin/bash
# pipelines/sibling/4-select/select.sh <deepseek|mimo>
# pipelines/sibling/archive/batch1-lane-pilot/select.sh unchanged except that every path is under pipelines/sibling/out/pipeline/, so batch-1's
# build/pipeline/selection_*.json is never overwritten. The driver model scores the sibling2 pool and
# picks its own top SELECT_N (default 50; SELECT-PROMPT.md holds {{N}}). Writes selection_<driver>.json.
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
D=${1:?usage: pipelines/sibling/4-select/select.sh <deepseek|mimo>}
R="$CWE_ROOT"; cd "$R" || exit 1
P=${LANE_PIPE:-pipelines/sibling/out/pipeline}   # the router sets LANE_PIPE for steps 2 and 3
mkdir -p "$P"
POOL=$P/pool.jsonl
[ -s "$POOL" ] || { echo "no pool ($POOL); run pipelines/sibling/4-select/lane.py pool" >&2; exit 2; }
# rubric + pool goes to claude via STDIN (over the 128KB single-argument limit)
PF=$P/select_prompt_$D.txt
N=${SELECT_N:-50}
case $N in ""|*[!0-9]*) echo "SELECT_N must be a number" >&2; exit 2;; esac
{ sed "s/{{N}}/$N/g" pipelines/sibling/4-select/SELECT-PROMPT.md; echo; cat "$POOL"; } > "$PF"
RAW=$P/selection_$D.raw.json
OUT=$P/selection_$D.json
date -u +%FT%TZ > $P/select_${D}_start.txt
timeout 2400 "$CWE_DRIVE" "$D" bash -c \
  'cat "$1" | "$HOME/.local/bin/claude" -p --model "$MODEL" --output-format json --max-turns 3' \
  _ "$PF" > "$RAW" 2> $P/select_$D.err
python3 - "$RAW" "$OUT" "$N" "$POOL" <<'PY'
import json, re, sys
raw, out, want = sys.argv[1], sys.argv[2], int(sys.argv[3])
pool = {str(json.loads(l)["entry_id"]) for l in open(sys.argv[4]) if l.strip()}
d = json.load(open(raw))
txt = d.get("result") or ""
m = re.search(r"\[\s*{.*}\s*\]", txt, re.S)
if not m:
    print("NO JSON ARRAY in model output; see", raw); sys.exit(1)
arr = [x for x in json.loads(m.group(0)) if isinstance(x, dict) and x.get("entry_id")]
seen, dup, alien = set(), 0, 0
uniq = []
for x in arr:
    k = str(x["entry_id"])
    if k not in pool:                       # an id the model made up or copied wrong
        alien += 1; continue
    if k in seen:
        dup += 1; continue
    seen.add(k); uniq.append(x)
json.dump(uniq, open(out, "w"), indent=1)
print(f"selected {len(uniq)} candidates (asked for {want}; {dup} repeated and {alien} unknown ids dropped) -> {out}")
PY
