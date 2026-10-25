#!/bin/bash
# mjml test fix (2026-10-24): gate task + control, then regrade every existing mjml run from its saved code.
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/ride_along.log; log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
s=stk-mjml-ghsa45h5; c=$s-control
log "$s: test fix applied (security/01 written-vs-resolved); gating task + control"
bash pipeline/gate_one_ds.sh "$s" >> "build/$s/testfix-20261024/gate.log" 2>&1; gs=$?
bash pipeline/gate_one_ds.sh "$c" >> "build/$c/testfix-20261024/gate.log" 2>&1; gc=$?
log "$s gate after test fix rc=$gs; control rc=$gc (0 = sound)"
[ "$gs" = 0 ] || { log "$s: gate not sound after the test fix; regrade NOT run (see build/$s/testfix-20261024/gate.log)"; exit 1; }
WHY="test fix 2026-10-24: security/01 resolved-target check now skips the case where the template wrote that path (audits: test-fault)"
for slug in "$s" "$c"; do
  for t in $(ls -d "$HOME/.tb-graders/cwe/jobs/$slug"-deepseek-r*/"$slug"__* "$HOME/.tb-graders/cwe/jobs/$slug"-mimo-r*/"$slug"__* 2>/dev/null); do
    case "$t" in *"$s-control-"*) [ "$slug" = "$s" ] && continue;; esac
    [ -d "$t/final-code" ] || { log "regrade skip (no final-code): ${t#*/jobs/}"; continue; }
    python3 build/regrade_from_code.py "$t" "$WHY" >> "build/$slug/testfix-20261024/regrade.log" 2>&1
    r=$(python3 -c "import json,glob,sys; f=sorted(glob.glob(sys.argv[1]+'/regrade-*/REGRADE.json'))[-1]; print(json.load(open(f)).get('reward'))" "$t" 2>/dev/null)
    log "regraded ${t#*/jobs/}: reward $r"
  done
done
log "$s: regrade done; re-audit the regraded runs (postmortem prepare uses the newest regrade)"
