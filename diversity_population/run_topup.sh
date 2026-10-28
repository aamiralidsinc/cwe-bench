#!/usr/bin/env bash
# Steps 1-4 for the top-up entries (extend_index.py), with the copied sourcer, the experiment index and data folder.
# repo-meta uses GITHUB_TOKEN from the environment when set (the caller reads it from .env; it is never printed).
set -u
cd "$(dirname "$0")/.."
D=diversity_population
S="python3 -I $D/copied/sourcer/osv_sourcer.py --data $HOME/.tb-graders/cwe/diversity-data --index $D/out/index/candidates.sqlite"
L=$D/out/steps_topup.log
: > $L
for step in "diffs --delay 1.0" "classify" "diffs --delay 1.0" "classify" "parents --limit 5000 --delay 1.2" \
            "repo-meta --limit 2000 --delay 0.3" "classify"; do
  echo "=== $(date -u +%FT%TZ) $step" >> $L
  $S $step >> $L 2>&1 || echo "exit $? for: $step" >> $L
done
echo "=== $(date -u +%FT%TZ) done" >> $L
