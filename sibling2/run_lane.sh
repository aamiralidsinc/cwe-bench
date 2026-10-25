#!/bin/bash
# sibling2/run_lane.sh <deepseek|mimo> [concurrency]
# pipeline/run_lane.sh for the sibling2 batch: reads sibling2/out/pipeline/slugs_<driver>.txt and runs
# sibling2/run_pipeline.sh (build -> gate -> .sound; ledger in sibling2/out/pipeline/) C at a time.
# Each worker sleeps 0-45 s before starting so the cold fill does not spin every container up at once.
set -uo pipefail
D=${1:?driver}; C=${2:-16}
R="$HOME/cwe-bench"; cd "$R" || exit 1
LIST="sibling2/out/pipeline/slugs_$D.txt"
[ -s "$LIST" ] || { echo "no slug list ($LIST); run sibling2/lane.py prepare $D" >&2; exit 2; }
echo "sibling2 lane $D: $(grep -c . "$LIST") candidates, concurrency $C, start $(date -u +%FT%TZ)"
grep -v '^$' "$LIST" | xargs -P "$C" -I '{}' bash -c 'sleep $((RANDOM % 46)); bash sibling2/run_pipeline.sh "$0" "{}"' "$D"
echo "sibling2 lane $D: DONE $(date -u +%FT%TZ)"
echo "=== verdict tally ==="
awk -F'\t' 'NR>1{print $3": "$4}' "sibling2/out/pipeline/ledger_$D.tsv" | sed 's/ (.*//' | sort | uniq -c
