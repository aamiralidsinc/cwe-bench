#!/bin/bash
# Idempotently wire the provenance snapshot into fairfix + harden (one line after the work-mkdir).
cd "$HOME/cwe-bench" || exit 1
for f in run_fairfix.sh pipeline/run_harden.sh; do
  if grep -q snapshot_experiment "$f"; then echo "$f: already wired"; continue; fi
  awk 'BEGIN{d=0} {print} /mkdir -p .*tb-graders.cwe.work.*SLUG/ && d==0 {print "bash pipeline/snapshot_experiment.sh \"$SLUG\"  # preserve prior version before in-place edit (provenance)"; d=1}' "$f" > "$f.tmp" && mv "$f.tmp" "$f" && chmod +x "$f" && echo "$f: wired"
done
echo "--- verify wiring ---"
grep -n snapshot_experiment run_fairfix.sh pipeline/run_harden.sh run_upgrade.sh
echo "--- syntax ---"
bash -n run_fairfix.sh && echo "run_fairfix.sh OK"
bash -n pipeline/run_harden.sh && echo "run_harden.sh OK"
