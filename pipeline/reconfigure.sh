#!/bin/bash
# One-shot: switch the running pilot to the staged queue (QUEUE.md). Keeps DS builds, pauses MM.
cd "$HOME/cwe-bench" || exit 1
echo "=== reconfigure $(date -u +%FT%TZ) ==="
pkill -f "[r]egate_unsound.sh" 2>/dev/null
pkill -f "trial.py.*--models mimo" 2>/dev/null          # premature stage-4b trials
pkill -f "[r]un_build.sh .*-mm" 2>/dev/null             # pause MM builds (stage 4)
for pl in build/*-mm/pipeline.log; do [ -e "$pl" ] || continue; s=$(basename "$(dirname "$pl")"); pkill -f -- "$s" 2>/dev/null; done
sleep 6
# clear incomplete mimo trial logs on ds-tasks so stage-4b re-trials fully (keep complete 3-run)
for pl in build/*-ds/runs_mimo.log; do [ -e "$pl" ] || continue; [ "$(grep -c reward= "$pl")" -lt 3 ] && : > "$pl"; done
# .sound/.unsound markers from the deepseek ledger (sound wins)
L=build/pipeline/ledger_deepseek.tsv
awk -F'\t' '$3=="gate" && $4 ~ /UNSOUND/{print $2}' "$L" | while read -r s; do [ -d "build/$s" ] && touch "build/$s/.unsound"; done
awk -F'\t' '$3=="gate" && $4 ~ /sound/ && $4 !~ /UNSOUND/{print $2}' "$L" | while read -r s; do [ -d "build/$s" ] && { rm -f "build/$s/.unsound"; touch "build/$s/.sound"; }; done
echo "markers: ds .sound=$(ls build/*-ds/.sound 2>/dev/null|wc -l) .unsound=$(ls build/*-ds/.unsound 2>/dev/null|wc -l)"
echo "keep: ds-builds=$(ps -eo cmd|grep -cE '[r]un_build.sh .*-ds') run_lane-ds=$(ps -eo cmd|grep -c '[r]un_lane.sh deepseek') | paused: mm-builds=$(ps -eo cmd|grep -cE '[r]un_build.sh .*-mm')"
C=6 nohup bash pipeline/queue.sh > build/pipeline/queue_master.log 2>&1 < /dev/null &
echo "QUEUE MASTER pid $!"
