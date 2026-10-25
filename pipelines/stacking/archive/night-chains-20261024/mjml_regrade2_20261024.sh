#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/ride_along.log; log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
s=stk-mjml-ghsa45h5
WHY="test fix 2026-10-24 (retry, grader as root): security/01 resolved-target check skips the case where the template wrote that path"
for t in $(ls -d "$HOME/.tb-graders/cwe/jobs/$s"-deepseek-r*/"$s"__* "$HOME/.tb-graders/cwe/jobs/$s"-mimo-r*/"$s"__*); do
  python3 build/regrade_from_code.py "$t" "$WHY" >> "build/$s/testfix-20261024/regrade.log" 2>&1
  f=$(ls -d "$t"/regrade-* | tail -1)
  log "regrade2 ${t#*/jobs/}: exit $(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('exit'), 'reward', d.get('reward'))" "$f/REGRADE.json")"
done
log "$s: regrade2 done"
