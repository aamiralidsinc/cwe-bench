#!/bin/bash
# postbuild.sh <slug> [--listing] : every post-build check of one built task, AT THE SAME TIME (2026-10-25).
#
#   gate       bash common/gate/gate_one_ds.sh <slug>         static, then nop/oracle/patches in parallel
#   blind fix  common/launch/drive.sh deepseek bash common/blindfix/run_blindfix.sh <slug>
#   listing    (--listing, stacking only) pipelines/stacking/4-listing/run_listing_check.sh, one retry on error
#
# The three start together. The blind fix adds checks/blind.patch to the manifest, which the gate's patch
# stage could not see, so when both the gate and the blind fix succeed the one blind patch check runs next
# (gate.py --only patches --patch blind.patch). The blind fix is best effort: if the agent fails, or its patch
# does not pass, the task can still be sound; that is recorded (blind_status.txt, .blind_fail) for review.
#
# Marker (exactly one, like gate_one_ds.sh): .sound (exit 0), .unsound (exit 1), .gate_error (exit 2);
# a stacking task whose instruction lists hidden traps under LISTING_ENFORCE gets .listing_fail (exit 3).
# On .sound the gate fingerprint is (re)written AFTER the blind patch is wired in, so it covers it.
# Progress: build/<slug>/postbuild.log.
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
. "$CWE_COMMON/markers.sh"     # marker helpers (common/markers.py, docs/STAGE-CONTRACTS.md)
S=${1:?usage: common/gate/postbuild.sh <slug> [--listing]}; LISTING=0; [ "${2:-}" = --listing ] && LISTING=1
cd "$CWE_ROOT" || exit 2
B="build/$S"; L="$B/postbuild.log"; mkdir -p "$B"
log() { echo "$(date -u +%FT%TZ) $S $*" | tee -a "$L"; }
log "postbuild: start (gate + blind fix${LISTING:+$([ $LISTING = 1 ] && echo ' + listing')} in parallel)"

# B2b file-time reset (owner decision 2 of 2026-10-28, reports/reward-hacking.md): before the first gate, insert the
# whole-tree time reset into environment/Dockerfile if the builder's Dockerfile lacks it. No gate fingerprint exists
# yet, so nothing goes stale (the script refuses when one does). Never blocks: it logs a "b2b:" line here.
python3 -I common/builder/tree_time_reset.py --postbuild "$S" >/dev/null 2>&1 || log "b2b: transformer exit $? (not blocking)"

( bash "$CWE_GATE_ONE" "$S" > "$B/postbuild.gate.out" 2>&1; echo $? > "$B/postbuild.gate.rc" ) &
pg=$!
( "$CWE_DRIVE" deepseek bash "$CWE_RUN_BLINDFIX" "$S" > "$B/postbuild.blind.out" 2>&1; echo $? > "$B/postbuild.blind.rc" ) &
pb=$!
pl=""
if [ "$LISTING" = 1 ]; then
  ( for try in 1 2; do
      "$CWE_DRIVE" deepseek bash pipelines/stacking/4-listing/run_listing_check.sh "$S" >> "$B/postbuild.listing.out" 2>&1
      python3 -I pipelines/stacking/4-listing/listing_verdict.py "$S" >> "$B/postbuild.listing.out" 2>&1; r=$?
      [ "$r" -ne 2 ] && break
    done; echo $r > "$B/postbuild.listing.rc" ) &
  pl=$!
fi
wait $pg; GRC=$(cat "$B/postbuild.gate.rc" 2>/dev/null || echo 2)
log "gate: $(tail -1 "$B/postbuild.gate.out") (exit $GRC)"
wait $pb; BRC=$(cat "$B/postbuild.blind.rc" 2>/dev/null || echo 9)
log "blind fix: exit $BRC ($(cat "$B/blind_status.txt" 2>/dev/null))"
LRC=0
if [ -n "$pl" ]; then
  wait $pl; LRC=$(cat "$B/postbuild.listing.rc" 2>/dev/null || echo 2)
  log "listing: $(python3 -I pipelines/stacking/4-listing/listing_verdict.py "$S" 2>/dev/null | head -1) (exit $LRC)"
fi

[ "$GRC" = 0 ] || { log "RESULT: not sound (gate exit $GRC)"; exit "$GRC"; }
# gate_one_ds.sh writes .sound as soon as the gate passes; hold it until every check below is done, so no
# trial launcher picks the task up in between (seen in the 2026-10-25 dry run).
cwe_hold_after_gate "$B"

# The blind patch, if the blind fix produced one: one more patch check, then the fingerprint covers it.
if [ "$BRC" = 0 ] && [ -f "$B/checks/blind.patch" ]; then
  python3 -I common/gate/gate.py "$S" --only patches --patch blind.patch --report gate_report.partial.blind.json >> "$L" 2>&1
  if python3 -c "import json,sys; sys.exit(0 if json.load(open('$B/gate_report.partial.blind.json')).get('verdict')=='pass' else 1)" 2>/dev/null; then
    log "blind patch check: pass"
  else
    # The blind agent works with everything in view (tests, reference, trap list), so a failing blind patch is a
    # warning that needs a look; it does not block (an agent can still slip). The file is moved aside (the gate
    # skips a declared blind patch with no file) and kept for review as checks/blind.failed.patch + .blind_fail.
    # The manifest keeps its declared blind entry (the static stage requires the declaration); without the
    # file the gate skips that check.
    mv -f "$B/checks/blind.patch" "$B/checks/blind.failed.patch"
    cwe_mark "$B" .blind_fail
    log "blind patch check: FAILED (kept as checks/blind.failed.patch, unwired; .blind_fail). Not blocking."
  fi
fi
python3 -I common/gate/fingerprint.py write "$S" >> "$L" 2>&1

if [ "$LISTING" = 1 ] && [ "$LRC" != 0 ]; then
  if [ -f pipelines/stacking/4-listing/LISTING_ENFORCE ]; then
    cwe_mark_listing_fail "$B"
    log "RESULT: gated, but the instruction lists hidden traps (or the check errored): .listing_fail, not sound"
    exit 3
  fi
  cwe_mark "$B" .listing_warn; log "listing (advisory, reviewer not calibrated): exit $LRC recorded in .listing_warn"
fi
cwe_mark_sound "$B"
log "RESULT: SOUND, ready for trials"
exit 0
