#!/bin/bash
# run_lane.sh <deepseek|mimo> [concurrency] [max_candidates]
# Runs the full pipeline over this lane's prepared slugs, <concurrency> in flight.
set -uo pipefail
D=${1:?driver}; C=${2:-8}; N=${3:-50}
R="$HOME/cwe-bench"; cd "$R" || exit 1
LIST="build/pipeline/slugs_$D.txt"
[ -s "$LIST" ] || { echo "no slug list ($LIST); run prepare_lane.py $D" >&2; exit 2; }
head -n "$N" "$LIST" | grep -v '^$' > "build/pipeline/run_$D.txt"
echo "lane $D: $(wc -l < build/pipeline/run_$D.txt) candidates, concurrency $C, start $(date -u +%FT%TZ)"
# xargs pool: one run_pipeline.sh per slug, C at a time. Each slot = build+gate+trial.
cat "build/pipeline/run_$D.txt" | xargs -P "$C" -I '{}' bash pipeline/run_pipeline.sh "$D" '{}'
echo "lane $D: DONE $(date -u +%FT%TZ)"
echo "=== lane $D verdict tally ==="
awk -F'\t' '$3=="trial"{print $4}' "build/pipeline/ledger_$D.tsv" | sort | uniq -c
