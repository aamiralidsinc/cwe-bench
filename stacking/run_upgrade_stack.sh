#!/bin/bash
# Stacking upgrade for ONE built stk- task (new, 2026-10-24; separate from run_stack_pipeline.sh, which
# is not used or changed). The stacking form of run_upgrade.sh, cut to its instruction step:
#   1. snapshot the control, then the task (provenance; moves this version's trial runs aside so the
#      new version is re-trialled from zero). Control first: its run folders share the task's prefix.
#   2. if there is no finished listing review, run one, so the agent sees what the report lists;
#   3. the agent rewrites ONLY tasks/SLUG/instruction.md (stacking/STACKING-UPGRADE-PROMPT.md);
#      Read/Grep/Glob/Edit/Write only, no Bash, no Docker;
#   4. any change outside instruction.md -> everything restored (exit 4);
#   5. listing check on the new report; one more rewrite round with the reviewer's labels on a FAIL;
#   6. copy the report to the control (build rule 13), static gate (leak scan) on both;
#   7. PASS: both keep .sound (tests, fix and image are unchanged, so the earlier container gate still
#      holds) and get .upgraded; trials pick them up as new versions. No rebuild, no container gate.
# Usage: ./drive.sh deepseek bash stacking/run_upgrade_stack.sh SLUG     Env: UPGRADE_TIMEOUT (3600 s/round)
# Exit 0 upgraded + listing PASS; 1 agent did not finish (restored); 2 refused (bad slug, busy);
#      3 agent changed nothing (restored); 4 touched other files or static gate failed (restored);
#      5 upgraded but the listing check still FAILs after 2 rounds (kept, no .sound, .listing_fail).
set -uo pipefail
SLUG=${1:?usage: stacking/run_upgrade_stack.sh SLUG}
R="$HOME/cwe-bench"; cd "$R" || exit 2
B=build/$SLUG; UL="$B/upgrade_stack.log"
log() { echo "$(date -u +%FT%TZ) $SLUG upgrade: $*" | tee -a "$UL"; }
[ -n "${MODEL:-}" ] || { echo "error: MODEL not set; launch via ./drive.sh deepseek bash stacking/run_upgrade_stack.sh $SLUG"; exit 2; }
case "$SLUG" in stk-*-control) echo "refused: $SLUG is a control; upgrade its stacked task"; exit 2;; stk-*) ;; *) echo "refused: not an stk- task"; exit 2;; esac
[ -f "$B/manifest.json" ] && [ -f "tasks/$SLUG/instruction.md" ] || { echo "refused: no manifest or instruction"; exit 2; }
[ -f "$B/.sound" ] || [ "${UPGRADE_FORCE:-0}" = 1 ] || { echo "refused: $SLUG is not gated sound (its container gate is what makes an instruction-only upgrade safe); re-gate it first, or UPGRADE_FORCE=1"; exit 2; }
CTL=$(python3 -c "import json,sys; print((json.load(open(sys.argv[1])).get('stacking') or {}).get('control_slug',''))" "$B/manifest.json")
[ -n "$CTL" ] && [ -f "tasks/$CTL/instruction.md" ] || { echo "refused: no control task"; exit 2; }
busy_pids() {
  local p a
  for p in /proc/[0-9]*; do
    a=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
    case "$a" in
      *"build/trial.py $SLUG "*|*"build/trial.py $CTL "*|*"run_stack_pipeline.sh $SLUG"*|*"run_fairfix_stack.sh $SLUG"*) echo "${p#/proc/}" ;;
    esac
  done
}
busy=$(busy_pids)
[ -z "$busy" ] || { echo "refused: $SLUG or its control is busy (pids $busy)"; exit 2; }

log "start (control $CTL)"
bash pipeline/snapshot_experiment.sh "$CTL" >> "$UL" 2>&1
bash pipeline/snapshot_experiment.sh "$SLUG" >> "$UL" 2>&1
restore() { bash pipeline/restore_snapshot.sh "$SLUG" "$1" >> "$UL" 2>&1; bash pipeline/restore_snapshot.sh "$CTL" "$1" >> "$UL" 2>&1; log "restored both to the trialled version: $1"; }
other() { { find "tasks/$SLUG" -type f ! -path "tasks/$SLUG/instruction.md"; find "tasks/$CTL" "$B/manifest.json" "$B/checks" -type f; } 2>/dev/null | LC_ALL=C sort | xargs -r sha256sum | sha256sum | cut -d" " -f1; }
ish() { sha256sum "tasks/$SLUG/instruction.md" | cut -c1-16; }
PRE=$(other); PRE_I=$(ish)
listing() { for t in 1 2; do bash stacking/run_listing_check.sh "$SLUG" >> "$UL" 2>&1; python3 -I stacking/listing_verdict.py "$SLUG" >> "$UL" 2>&1; LST=$?; [ "$LST" -ne 2 ] && break; done; }

if [ "$(cat "$B/listing_status.txt" 2>/dev/null)" != ok ]; then log "no finished listing review; running one first"; listing; fi
log "listing before: $(python3 -I stacking/listing_verdict.py "$SLUG" | head -1)"
LST=1
for round in 1 2; do
  P="$(sed -n "/^---8<---$/,\$p" stacking/STACKING-UPGRADE-PROMPT.md | tail -n +2 | sed "s#{{ROOT}}#$R#g; s#{{SLUG}}#$SLUG#g")"
  [ "$round" = 2 ] && P="$P

**Second round.** The reviewer re-checked your first rewrite; $R/$B/listing.json now holds its labels
for the CURRENT report. Rewrite again so every hidden trap it still labels NAMED or DESCRIBED becomes
GENERAL or ABSENT, under the same rules."
  timeout "${UPGRADE_TIMEOUT:-3600}" "$HOME/.local/bin/claude" -p "$P" --model "$MODEL" \
    --restricted --safe-mode --strict-mcp-config --no-session-persistence \
    --tools "Read,Grep,Glob,Edit,Write" --permission-mode acceptEdits --add-dir "$R" \
    --output-format json > "$B/upgrade_stack-run$round.json" 2> "$B/upgrade_stack-run$round.err"
  rc=$?
  st=$(python3 pipeline/agent_status.py "$B/upgrade_stack-run$round.json" "$rc")
  [ "$st" = ok ] || { restore "round $round agent did not finish: $st"; echo "not finished: $st" > "$B/upgrade_stack_status.txt"; exit 1; }
  [ "$(other)" = "$PRE" ] || { restore "round $round changed files other than instruction.md"; echo "touched other files" > "$B/upgrade_stack_status.txt"; exit 4; }
  if [ "$round" = 1 ] && [ "$(ish)" = "$PRE_I" ]; then restore "agent changed nothing"; echo unchanged > "$B/upgrade_stack_status.txt"; exit 3; fi
  listing
  log "round $round listing: $(python3 -I stacking/listing_verdict.py "$SLUG" | head -1)"
  [ "$LST" -eq 0 ] && break
done

cp "tasks/$SLUG/instruction.md" "tasks/$CTL/instruction.md"
for s in "$SLUG" "$CTL"; do
  python3 -I builder/gate.py "$s" --only static >> "$UL" 2>&1
  res=$(python3 - "build/$s/gate_report.partial.json" "$s" <<'PY'
import json, sys
try:
    r = json.load(open(sys.argv[1]))
except Exception as e:
    print(f"internal\tstatic report unreadable: {e}"); sys.exit()
if r.get("slug") != sys.argv[2] or r.get("only") != "static":
    print("internal\tstale or foreign static report"); sys.exit()
if r.get("verdict") == "pass":
    print("pass\t"); sys.exit()
deferred = ("FAIRNESS.md missing", "kind='blind'")   # deferred by the fairness-after-trial policy, as in run_upgrade.sh
probs = [p for p in str(r.get("failure", "")).split("; ") if p and not any(d in p for d in deferred)]
print(("task\t" + "; ".join(probs)) if probs else "pass\tonly deferred strict items")
PY
)
  kind=${res%%$'\t'*}; why=${res#*$'\t'}
  log "static $s: $kind${why:+ ($why)}"
  [ "$kind" = pass ] || { restore "static gate on $s: $kind $why"; echo "static failed on $s: $why" > "$B/upgrade_stack_status.txt"; exit 4; }
done

V=$(cat "$B/VERSION")
if [ "$LST" -ne 0 ]; then
  for s in "$SLUG" "$CTL"; do rm -f "build/$s/.sound"; touch "build/$s/.listing_fail"; done
  echo "upgraded to $V but the listing check still FAILs after 2 rounds; not sound (v1 is in the snapshot)" > "$B/upgrade_stack_status.txt"
  log "$(cat "$B/upgrade_stack_status.txt")"; exit 5
fi
for s in "$SLUG" "$CTL"; do rm -f "build/$s/.listing_fail" "build/$s/.listing_warn"; echo "$V $(date -u +%FT%TZ)" > "build/$s/.upgraded"; done
echo "upgraded to $V; listing PASS; static ok on both; ready for re-trial" > "$B/upgrade_stack_status.txt"
log "$(cat "$B/upgrade_stack_status.txt")"
exit 0
