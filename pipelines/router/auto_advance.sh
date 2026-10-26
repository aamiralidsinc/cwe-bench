#!/bin/bash
# auto_advance.sh : the per-heartbeat pipeline steps that need no person (owner decision 2026-10-26). Run on the VM.
#  1. fairness: every BREAKER candidate of the scale run without a FAIRNESS.md newer than its last trial gets a
#     fairness review (stacking: 7-fairness/run_fairness_stack.sh; sibling: 9-fairness/run_fairness.sh), on DeepSeek.
#  2. audits: every failing run awaiting audit (except tasks both models solved) gets its evidence folder prepared
#     (common/audit/postmortem.py prepare); the list goes to pipelines/router/out/queue/audit_ready.txt for the
#     Opus auditors (sub-agents of the controlling session; audits are never run by a CLI).
#  3. step 3: route stacked tasks any model solved (router step3) and prepare their sibling builds.
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
cd "$CWE_ROOT" || exit 1
L=pipelines/router/out/queue/auto_advance.log; Q=pipelines/router/out/queue
python3 common/audit/audit_results.py > /dev/null 2>&1 || echo "$(date -u +%FT%TZ) ledger rebuild FAILED" >> $L
scale=$(cat pipelines/router/out/batches/*.txt | sed 's/#.*//' | awk 'NF{print $1}' | sort -u)
# 1. fairness
for s in $scale; do
  grep -q "| $s | .*BREAKER candidate" build/audit/ledger.md || continue
  pgrep -f "run_fairness(_stack)?\.sh $s$" >/dev/null && continue
  last=$(ls -dt ~/.tb-graders/cwe/jobs/$s-*/ 2>/dev/null | head -1)
  if [ -f build/$s/FAIRNESS.md ] && [ -n "$last" ] && [ build/$s/FAIRNESS.md -nt "$last" ]; then continue; fi
  case $s in stk-*) cmd="pipelines/stacking/7-fairness/run_fairness_stack.sh" ;; *) cmd="pipelines/sibling/9-fairness/run_fairness.sh" ;; esac
  setsid nohup common/launch/drive.sh deepseek bash $cmd $s > build/$s/fairness.nohup 2>&1 < /dev/null &
  echo "$(date -u +%FT%TZ) fairness started: $s" >> $L; sleep 5
done
# 2. audits
python3 common/audit/postmortem.py pending 2>/dev/null > /tmp/aa_pending.txt
: > $Q/audit_ready.new
while read -r d; do
  [ -n "$d" ] || continue
  job=$(basename "$(dirname "$d")"); task=$(echo "$job" | sed -E 's/-(deepseek|mimo)-r[0-9]+-.*$//')
  grep -q "| $task | .*rejected (both solved)" build/audit/ledger.md && continue
  ls -d "$d"/postmortem-*/ >/dev/null 2>&1 && pm=$(ls -dt "$d"/postmortem-*/ | head -1) && [ ! -f "$pm/POSTMORTEM.json" ] && [ ! -f "$pm/verdict.json" ] && { echo "${pm%/}" >> $Q/audit_ready.new; continue; }
  out=$(python3 common/audit/postmortem.py prepare "$d" 2>/dev/null | tail -1); [ -d "$out" ] && echo "$out" >> $Q/audit_ready.new
done < /tmp/aa_pending.txt
mv $Q/audit_ready.new $Q/audit_ready.txt
# 3. step 3
python3 -I pipelines/router/route.py step3 2>&1 | grep -E "^step 3|wait for a screen" >> $L
if grep -q "newly routed" $L 2>/dev/null && [ -s pipelines/router/out/step3/pipeline/selection_deepseek.json ]; then
  LANE_RECS=pipelines/router/out/step3/screener LANE_PIPE=pipelines/router/out/step3/pipeline LANE_SUFFIX=s3 \
    python3 -I pipelines/sibling/4-select/lane.py prepare deepseek > /dev/null 2>&1
fi
echo "$(date -u +%FT%TZ) auto_advance: audits ready $(wc -l < $Q/audit_ready.txt)" >> $L
echo "audits ready: $(wc -l < $Q/audit_ready.txt) | fairness running: $(pgrep -fc 'run_fairness')"
