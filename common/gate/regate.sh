#!/bin/bash
# regate.sh <slug> [--listing] : the gate part of postbuild.sh again, reusing the blind fix and listing results
# that already exist (2026-10-26). For tasks whose post-build gate was stopped or broke for reasons outside the
# task (overload, a killed process): runs gate_one_ds.sh, then the blind patch check if checks/blind.patch was
# wired, then the gate fingerprint, then the listing decision from the existing listing review, and marks
# .sound. Same markers and exit codes as postbuild.sh. Throttle with GATE_PARALLEL (Harbor runs per stage).
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
S=${1:?usage: common/gate/regate.sh <slug> [--listing]}; LISTING=0; [ "${2:-}" = --listing ] && LISTING=1
cd "$CWE_ROOT" || exit 2
B="build/$S"; L="$B/postbuild.log"
log() { echo "$(date -u +%FT%TZ) $S $*" | tee -a "$L"; }
log "regate: start (GATE_PARALLEL=${GATE_PARALLEL:-all}; blind fix and listing reused)"
bash "$CWE_GATE_ONE" "$S" > "$B/regate.gate.out" 2>&1; GRC=$?
log "regate gate: $(tail -1 "$B/regate.gate.out") (exit $GRC)"
[ "$GRC" = 0 ] || { log "RESULT: not sound (regate gate exit $GRC)"; exit "$GRC"; }
mv -f "$B/.sound" "$B/.gate_passed" 2>/dev/null
if [ -f "$B/checks/blind.patch" ]; then
  python3 -I common/gate/gate.py "$S" --only patches --patch blind.patch --report gate_report.partial.blind.json >> "$L" 2>&1
  if python3 -c "import json,sys; sys.exit(0 if json.load(open('$B/gate_report.partial.blind.json')).get('verdict')=='pass' else 1)" 2>/dev/null; then
    log "blind patch check: pass"
  else
    mv -f "$B/checks/blind.patch" "$B/checks/blind.failed.patch"; touch "$B/.blind_fail"
    log "blind patch check: FAILED (kept as checks/blind.failed.patch, unwired; .blind_fail). Not blocking."
  fi
fi
python3 -I common/gate/fingerprint.py write "$S" >> "$L" 2>&1
if [ "$LISTING" = 1 ]; then
  python3 -I pipelines/stacking/4-listing/listing_verdict.py "$S" > /dev/null 2>&1; LRC=$?
  if [ "$LRC" != 0 ] && [ -f pipelines/stacking/4-listing/LISTING_ENFORCE ]; then
    rm -f "$B/.sound" "$B/.gate_passed" "$B/.listing_warn"; touch "$B/.listing_fail"
    log "RESULT: gated, but the listing review FAILs (exit $LRC): .listing_fail, not sound"; exit 3
  fi
fi
rm -f "$B/.gate_passed"; touch "$B/.sound"
log "RESULT: SOUND, ready for trials (regate)"
exit 0
