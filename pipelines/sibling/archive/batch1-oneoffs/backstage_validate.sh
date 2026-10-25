#!/bin/bash
# Wait for backstage-ds fairfix, then re-gate and re-trial BOTH models. Writes the verdict to a log.
# Detached (setsid) so it survives ssh drops. An unfinished fairfix stops it (the task is restored);
# the task is gated before any trial (until 2026-10-20 this marked it .sound with no gate).
cd "$HOME/cwe-bench" || exit 1
. pipeline/validate_common.sh
S=backstage-ds
LOG=build/pipeline/backstage_validate.log
echo "=== validate $S start $(date -u +%FT%TZ) ===" >> "$LOG"
while [ "$(ps -eo cmd | grep -c "[r]un_fairfix.sh $S")" -gt 0 ]; do sleep 60; done
st=$(cat build/$S/fairfix_status.txt 2>/dev/null || echo "no fairfix_status.txt")
echo "fairfix done $(date -u +%T): $st" >> "$LOG"
[ "$st" = ok ] || { echo "STOPPED: fairfix did not finish cleanly ($st)" >> "$LOG"; exit 1; }
echo "re-gating, then re-trialing both models $(date -u +%T)" >> "$LOG"
gate_then_trial "$S" "$LOG" || { echo "STOPPED: not sound after fairfix" >> "$LOG"; exit 1; }
echo "RE-TRIAL RESULT $(date -u +%T): $(both_verdict "$S")" >> "$LOG"
