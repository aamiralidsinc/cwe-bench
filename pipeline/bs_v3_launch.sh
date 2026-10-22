#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
L=build/backstage-ds/v3-airtight.log; : > "$L"
echo "=== backstage-ds v3 airtight START $(date -u +%FT%TZ) ===" >> "$L"
# 1) launch v3 re-trial (3h timeout, both models, early-abort)
rm -f build/backstage-ds/.terminal build/backstage-ds/.auto_trialed; touch build/backstage-ds/.auto_trialed
echo "[v3 trial launch $(date -u +%T)]" >> build/backstage-ds/auto_trial.out
setsid bash -c "cd \$HOME/cwe-bench; CWE_AGENT_TIMEOUT_MULT=1 python3 build/trial.py backstage-ds >> build/backstage-ds/auto_trial.out 2>&1; echo \"[trial-done backstage-ds v3 \$(date -u +%T)]\" >> build/pipeline/auto_trial.log" >/dev/null 2>&1 </dev/null &
echo "[1] v3 trial launched" >> "$L"
# 2) add backstage case to the in-container blind generator (backup first)
cp pipeline/blind_informed_ctr.sh pipeline/blind_informed_ctr.sh.bak-$(date -u +%Y%m%dT%H%M%SZ)
IMGB=$(docker images --format "{{.CreatedAt}}|{{.Repository}}:{{.Tag}}" | grep -i "backstage-ds" | sort -r | head -1 | cut -d"|" -f2)
python3 - "$IMGB" <<'PY'
import sys
p="pipeline/blind_informed_ctr.sh"; img=sys.argv[1]; s=open(p).read()
if "  backstage-ds)" not in s:
    branch=('  backstage-ds)\n'
            f'    IMG="{img}"\n'
            "    BUILD_CMD='ESB=/app/node_modules/esbuild/bin/esbuild; ok=1; for f in $(cd /app && git diff --name-only 2>/dev/null | grep \"[.]ts$\"); do \"$ESB\" --log-level=warning --loader:.ts=ts /app/$f >/dev/null || { echo PARSE-FAIL $f; ok=0; }; done; [ $ok = 1 ] && echo \"all edited TS modules parse OK\"' ;;\n")
    s=s.replace('case "$SLUG" in\n','case "$SLUG" in\n'+branch,1)
    open(p,"w").write(s); print("backstage case added, IMG="+img)
else: print("backstage case already present")
PY
echo "[2] generator patched (IMG=$IMGB)" >> "$L"
# 3) generate blind.patch in-container, then FULL gate
echo "[3] blind gen start $(date -u +%T)" >> "$L"
bash pipeline/blind_informed_ctr.sh backstage-ds >> "$L" 2>&1
echo "[3] blind gen done $(date -u +%T); blind.patch=$(wc -l < build/backstage-ds/checks/blind.patch 2>/dev/null || echo 0)L" >> "$L"
python3 - <<'PY'
import json
p="build/backstage-ds/manifest.json"; m=json.load(open(p)); pc=m.setdefault("patch_checks",[])
if not any(c.get("patch")=="blind.patch" for c in pc):
    pc.append({"patch":"blind.patch","expect":"pass","kind":"blind","why":"informed blind fix (instruction+code+traps, no tests), in-container verified"})
    json.dump(m,open(p,"w"),indent=1); print("manifest: blind.patch wired")
PY
echo "[4] full gate start $(date -u +%T)" >> "$L"
bash pipeline/gate_one_ds.sh backstage-ds >> "$L" 2>&1
echo "[4] full gate done $(date -u +%T): sound=$([ -f build/backstage-ds/.sound ]&&echo Y||echo N) unsound=$([ -f build/backstage-ds/.unsound ]&&echo Y||echo N)" >> "$L"
echo "V3-AIRTIGHT-GATE-DONE" >> "$L"
