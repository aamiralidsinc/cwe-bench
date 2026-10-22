#!/bin/bash
# backstage-ds after the test-mock fix: confirm blind / oracle / nop on the real tests, then re-gate.
cd "$HOME/cwe-bench" || exit 1
L=build/pipeline/backstage_testfix-$(date -u +%Y%m%dT%H%M%SZ).log
echo "=== backstage-ds test-fix verify start $(date -u +%FT%TZ)" >> "$L"
for p in blind.patch oracle nop; do
  bash pipeline/rca_rerun.sh backstage-ds "$p" > /tmp/bs_rca_$p.out 2>&1
  d=$(ls -dt build/backstage-ds/rca/*-"${p%.patch}" | head -1)
  r=$(python3 -c "import json,sys;r=json.load(open(sys.argv[1]));print(r.get('reward'), {g:f\"{sum(v=='pass' for v in r[g].values())}/{len(r[g])}\" for g in ('security','functional')})" "$d/verifier/results.json" 2>&1)
  echo "[verify $p] $r  ($d/report.txt) $(date -u +%T)" >> "$L"
done
echo "[gate] $(bash pipeline/gate_one_ds.sh backstage-ds 2>&1 | tail -1) $(date -u +%T)" >> "$L"
echo "=== done $(date -u +%FT%TZ)" >> "$L"
