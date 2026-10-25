#!/bin/bash
# pipelines/sibling/6-build/run_lane.sh <deepseek|mimo> [concurrency]
# pipelines/sibling/archive/batch1-lane-pilot/run_lane.sh for the sibling2 batch: reads pipelines/sibling/out/pipeline/slugs_<driver>.txt and runs
# pipelines/sibling/6-build/run_pipeline.sh (build -> gate -> .sound; ledger in pipelines/sibling/out/pipeline/) C at a time.
# Each worker sleeps 0-45 s before starting so the cold fill does not spin every container up at once.
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
D=${1:?driver}; C=${2:-16}
R="$CWE_ROOT"; cd "$R" || exit 1
LIST="$CWE_SIBLING_OUT/pipeline/slugs_$D.txt"
[ -s "$LIST" ] || { echo "no slug list ($LIST); run pipelines/sibling/4-select/lane.py prepare $D" >&2; exit 2; }
echo "sibling2 lane $D: $(grep -c . "$LIST") candidates, concurrency $C, start $(date -u +%FT%TZ)"
grep -v '^$' "$LIST" | xargs -P "$C" -I '{}' bash -c 'sleep $((RANDOM % 46)); bash pipelines/sibling/6-build/run_pipeline.sh "$0" "{}"' "$D"
echo "sibling2 lane $D: DONE $(date -u +%FT%TZ)"
echo "=== verdict tally ==="
awk -F'\t' 'NR>1{print $3": "$4}' "$CWE_SIBLING_OUT/pipeline/ledger_$D.tsv" | sed 's/ (.*//' | sort | uniq -c
