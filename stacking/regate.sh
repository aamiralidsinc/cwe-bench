#!/bin/bash
# Targeted re-gate: skip the (already-successful) agent build, re-run gate->blindfix->gate->sound.
# For tasks whose ONLY failure was the now-fixed no-network gate infra error. Artifacts must be present.
set -uo pipefail
SLUG=${1:?usage: regate.sh SLUG}
R="$HOME/cwe-bench"; cd "$R" || exit 1
L="build/$SLUG/stack_pipeline.log"; mkdir -p "build/$SLUG"
log() { echo "$(date -u +%FT%TZ) $SLUG REGATE $*" | tee -a "$L"; }
gate_ok() { python3 -c "import json,sys; sys.exit(0 if json.load(open('build/$1/gate_report.json')).get('passed') else 1)" 2>/dev/null; }

[ -f "build/$SLUG/manifest.json" ] || { log "STOP: no manifest (needs full rebuild)"; exit 1; }
[ -d "tasks/$SLUG" ]              || { log "STOP: no task dir (needs full rebuild)"; exit 1; }
rm -f "build/$SLUG/.sound"

python3 -I stacking/normalize_expect.py "$SLUG" >> "$L" 2>&1 || true
log "check: stacking static check"
python3 -I stacking/check_stack.py "$SLUG" >> "$L" 2>&1 || { log "STOP: check_stack failed"; exit 1; }
CTL=$(python3 -c "import json; print((json.load(open('build/$SLUG/manifest.json')).get('stacking') or {}).get('control_slug',''))")
[ -n "$CTL" ] || { log "STOP: manifest has no stacking.control_slug"; exit 1; }

log "gate: $SLUG"
python3 -I builder/gate.py "$SLUG" >> "$L" 2>&1
gate_ok "$SLUG" || { log "STOP: gate failed for $SLUG"; exit 1; }

log "blind fix: $SLUG"
./drive.sh deepseek bash run_blindfix.sh "$SLUG" >> "$L" 2>&1
python3 -I builder/gate.py "$SLUG" --only patches >> "$L" 2>&1
gate_ok "$SLUG" || { log "STOP: patch checks failed after the blind fix"; exit 1; }

touch "build/$SLUG/.sound"
log "SOUND: $SLUG ready for trials"

log "gate: $CTL (control)"
python3 -I builder/gate.py "$CTL" >> "$L" 2>&1
if gate_ok "$CTL"; then touch "build/$CTL/.sound"; log "SOUND: $CTL (control) ready for trials"; else log "WARN: control $CTL gate failed"; fi
