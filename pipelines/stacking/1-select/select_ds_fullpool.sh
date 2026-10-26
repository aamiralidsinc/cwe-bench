#!/bin/bash
# Full-pool stacking selection on DeepSeek screens (2026-10-25). Run on the VM from the repo root.
# Rebuilds out/screener-ds/ (derived, not committed), ranks H4 and writes out/reader_jobs_ds.jsonl. Then:
#   common/launch/drive.sh deepseek bash -c "CLAUDE_BIN=$HOME/.local/bin/claude python3 -I pipelines/stacking/1-select/run_reader.py --parallel 70 --model \"$MODEL\" --outdir pipelines/stacking/out/reader-ds --jobs-file pipelines/stacking/out/reader_jobs_ds.jsonl"
#   python3 -I pipelines/stacking/1-select/score_stack.py --reader-dir pipelines/stacking/out/reader-ds
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
cd "$CWE_ROOT" || exit 1; O=pipelines/stacking/out
# 1. keep batch 1's selection files
B=$O/batch1-selection-20261025; mkdir -p $B
for f in h4_candidates.tsv h4_shortlist.md reader_jobs.jsonl stack_scores.md stack_scores.tsv; do [ -f $O/$f ] && [ ! -f $B/$f ] && cp -p $O/$f $B/; done
# 2. one folder of DeepSeek screens only: the 221 new + the 550 re-screens
D=$O/screener-ds; mkdir -p $D
python3 - <<PY
import json, glob, os, shutil
O="$O"; D="$D"; n=0
for src in (O+"/screener", O+"/screener-ds-rescreen"):
    for f in glob.glob(src+"/*.json"):
        b=os.path.basename(f)
        if b.startswith(("_",".")) or b.endswith(".run.json"): continue
        try: m=str(json.load(open(f)).get("model","")).lower()
        except Exception: continue
        if "deepseek" in m:
            shutil.copy2(f, os.path.join(D,b)); n+=1
print("DeepSeek screens in", D, ":", n)
PY
# 3. H4 ranking on DeepSeek screens
python3 -I pipelines/stacking/1-select/h4_rank.py --recs $D --built tasks 2>&1 | tail -15
# 4. reader jobs: every eligible H4 host and every ready H3 pair in an unbuilt repo
python3 -I pipelines/stacking/1-select/make_reader_jobs.py --h4 0 --h3 0 --recs $D --jobs-out $O/reader_jobs_ds.jsonl --built tasks 2>&1 | tail -4
