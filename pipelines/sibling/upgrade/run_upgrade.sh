#!/bin/bash
# Upgrade one already-built task to BETTER-PATTERNS §2-§8 (reuse image where possible, re-gate).
# Rewrites instruction.md to one general property, ensures >=1 how-type lever, extends tests/checks/
# oracle; rebuilds the image ONLY if repo code changed. Needs Bash+Docker -> bypassPermissions ->
# a PERSON (or common/launch/drive.sh) launches this. Usage: common/launch/drive.sh deepseek bash pipelines/sibling/upgrade/run_upgrade.sh SLUG
# Env: MODEL (required; common/launch/drive.sh sets the lane model), UPGRADE_TIMEOUT (10800).
# Exit 0 = upgraded and gated sound; 1 = the agent did not finish (task restored); 3 = the agent
# changed nothing (restored); 4 = upgraded but the gate did not pass (see upgrade-gate.log).
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
SLUG=${1:?usage: pipelines/sibling/upgrade/run_upgrade.sh SLUG}
cd "$CWE_ROOT" || exit 1
B=build/$SLUG; GL="$B/upgrade-gate.log"
[ -n "${MODEL:-}" ] || { echo "error: MODEL not set; launch via common/launch/drive.sh deepseek bash pipelines/sibling/upgrade/run_upgrade.sh $SLUG" | tee "$B/upgrade_status.txt"; exit 1; }
echo "running" > "$B/upgrade_status.txt"
mkdir -p "$HOME/.tb-graders/cwe/work/$SLUG"
# Preserve the current version (task + its trial runs) as a separate experiment BEFORE editing,
# and bump build/$SLUG/VERSION. Provenance in ~/.tb-graders/cwe/experiments/$SLUG/ + INDEX.tsv.
bash "$CWE_SNAPSHOT" "$SLUG"
# Fingerprint the GATE-RELEVANT files (not instruction.md) before the edit, to decide the gate after.
REL="tasks/$SLUG/tests tasks/$SLUG/solution tasks/$SLUG/environment $B/checks $B/manifest.json"
fp() { find $@ -type f 2>/dev/null | sort | xargs cat 2>/dev/null | sha256sum | cut -d' ' -f1; }
PRE=$(fp $REL); PRE_ALL=$(fp tasks/$SLUG $B/checks $B/manifest.json)
P=$(sed "s/{{SLUG}}/$SLUG/g; s#{{ROOT}}#$CWE_ROOT#g" pipelines/sibling/upgrade/UPGRADE-PROMPT.md)
date -u +%FT%TZ > "$B/upgrade_start.txt"
timeout "${UPGRADE_TIMEOUT:-10800}" "$HOME/.local/bin/claude" -p "$P" --model "$MODEL" \
  --permission-mode bypassPermissions --add-dir "$CWE_ROOT" --add-dir "$HOME/.tb-graders/cwe/work" \
  --output-format json > "$B/upgrade-run.json" 2> "$B/upgrade-run.err"
rc=$?
echo $rc > "$B/upgrade-exit.txt"
date -u +%FT%TZ > "$B/upgrade_end.txt"
st=$(python3 "$CWE_AGENT_STATUS" "$B/upgrade-run.json" "$rc" --details "$B/upgrade_status.json")
if [ "$st" != ok ]; then
  echo "$st" > "$B/upgrade_status.txt"; bash "$CWE_RESTORE" "$SLUG" "upgrade: $st"
  echo "$SLUG upgrade: NOT done ($st); task restored"; exit 1
fi
if [ "$(fp tasks/$SLUG $B/checks $B/manifest.json)" = "$PRE_ALL" ]; then
  echo "unchanged" > "$B/upgrade_status.txt"; bash "$CWE_RESTORE" "$SLUG" "upgrade: agent changed nothing"
  echo "$SLUG upgrade: agent changed nothing; restored"; exit 3
fi
# CONDITIONAL GATE: full container gate only if a gate-relevant file changed; else static-only (0 containers).
code=0
if [ "$(fp $REL)" = "$PRE" ]; then
  echo "$SLUG: instruction-only upgrade -> static gate only (0 containers)" | tee -a "$GL"
  python3 -I "$CWE_GATE" "$SLUG" --only static >> "$GL" 2>&1
  # The strict-gate items that the fairness-after-trial policy (2026-10-19) defers are warnings
  # here; any OTHER static problem (a leak, a missing file) means the new instruction is not sound.
  res=$(python3 - "$B/gate_report.partial.json" "$SLUG" <<'PY'
import json, sys
r = json.load(open(sys.argv[1])); slug = sys.argv[2]
if r.get("slug") != slug or r.get("only") != "static":
    print("internal\tstale or foreign static report"); sys.exit()
if r.get("verdict") == "pass":
    print("pass\t"); sys.exit()
deferred = ("FAIRNESS.md missing", "kind='blind'")
probs = [p for p in str(r.get("failure", "")).split("; ") if p and not any(d in p for d in deferred)]
print(("task\t" + "; ".join(probs)) if probs else "pass\tonly deferred strict items")
PY
)
  kind=${res%%$'\t'*}; why=${res#*$'\t'}
  echo "static: $kind${why:+ ($why)}" >> "$GL"
  case "$kind" in
    pass) echo "upgraded (instruction only; static ok)" > "$B/upgrade_status.txt" ;;
    task) rm -f "$B/.sound"; touch "$B/.unsound"; echo "upgraded but static failed: $why" > "$B/upgrade_status.txt"; code=4 ;;
    *)    echo "upgraded; static gate could not be read: $why" > "$B/upgrade_status.txt"; code=4 ;;
  esac
else
  echo "$SLUG: gate-relevant files changed -> full container gate" | tee -a "$GL"
  bash "$CWE_GATE_ONE" "$SLUG" >> "$GL" 2>&1 \
    && echo "upgraded and gated sound" > "$B/upgrade_status.txt" \
    || { echo "upgraded; gate: $(tail -1 "$GL")" > "$B/upgrade_status.txt"; code=4; }
fi
echo "$SLUG upgrade: $(cat "$B/upgrade_status.txt")"
exit $code
