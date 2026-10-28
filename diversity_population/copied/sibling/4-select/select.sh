#!/bin/bash
# diversity_population copy of pipelines/sibling/4-select/select.sh.
#   select.sh <deepseek|mimo> <pool.jsonl> <out_dir> [N]
# Changes from the original: no common/paths.sh; the pool, output folder and N are arguments; the copied
# drive.sh and SELECT-PROMPT.md are used; the claude binary comes from CLAUDE_BIN. The model call, the prompt
# assembly and the parsing of the answer are unchanged.
set -uo pipefail
D=${1:?usage: select.sh <deepseek|mimo> <pool.jsonl> <out_dir> [N]}; POOL=${2:?pool}; P=${3:?out_dir}; N=${4:-12}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CLAUDE_BIN=${CLAUDE_BIN:-$HOME/.local/bin/claude}
mkdir -p "$P"
# macOS has no timeout(1): fall back to gtimeout, then to a perl alarm wrapper
if command -v timeout >/dev/null; then TIMEOUT=timeout; elif command -v gtimeout >/dev/null; then TIMEOUT=gtimeout
else TIMEOUT="perl -e alarm(shift);exec(@ARGV)"; fi
[ -s "$POOL" ] || { echo "no pool ($POOL)" >&2; exit 2; }
case $N in ""|*[!0-9]*) echo "N must be a number" >&2; exit 2;; esac
PF=$P/select_prompt_$D.txt
{ sed "s/{{N}}/$N/g" "$HERE/SELECT-PROMPT.md"; echo; cat "$POOL"; } > "$PF"
RAW=$P/selection_$D.raw.json
OUT=$P/selection_$D.json
date -u +%FT%TZ > $P/select_${D}_start.txt
$TIMEOUT 2400 "$HERE/../../launch/drive.sh" "$D" bash -c \
  'cat "$1" | "$2" -p --model "$MODEL" --output-format json --max-turns 3' \
  _ "$PF" "$CLAUDE_BIN" > "$RAW" 2> $P/select_$D.err
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
