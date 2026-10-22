#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
GL=build/pipeline/regate_parallel.log; BL=build/pipeline/blind_informed_batch.log
: > "$GL"; : > "$BL"
echo "=== PARALLEL recover START $(date -u +%FT%TZ) ===" >> "$GL"
# Group-A remaining (astro already gating serially) + coreutils (new informed patch) -> parallel gates, jittered
GA="flyto-core-ds keras-ds fission-ds portainer-ds coreutils-ds"
printf '%s\n' $GA | xargs -P5 -I{} bash -c '
  s="$1"; cd "$HOME/cwe-bench"; sleep $((RANDOM%12))
  echo "[gate-start $s $(date -u +%T)]" >> build/pipeline/regate_parallel.log
  bash pipeline/gate_one_ds.sh "$s" >> build/pipeline/regate_parallel.log 2>&1
  echo "[RESULT $s] sound=$([ -f build/$s/.sound ]&&echo Y||echo N) unsound=$([ -f build/$s/.unsound ]&&echo Y||echo N)" >> build/pipeline/regate_parallel.log
' _ {} &
# Group-B other 6: generate informed blind (Opus) THEN re-gate, parallel, jittered
GB="knowns-ds openbao-ds orval-ds tinacms-ds vibe-trading-ds yamcs-ds"
printf '%s\n' $GB | xargs -P6 -I{} bash -c '
  s="$1"; cd "$HOME/cwe-bench"; sleep $((RANDOM%15))
  echo "[gen-start $s $(date -u +%T)]" >> build/pipeline/blind_informed_batch.log
  bash pipeline/blind_informed.sh "$s" >> build/pipeline/blind_informed_batch.log 2>&1
  echo "[gen-done $s $(date -u +%T)] patch=$([ -s build/$s/checks/blind.patch ]&&wc -l <build/$s/checks/blind.patch||echo 0)L -> re-gating" >> build/pipeline/blind_informed_batch.log
  bash pipeline/gate_one_ds.sh "$s" >> build/pipeline/blind_informed_batch.log 2>&1
  echo "[RESULT $s] sound=$([ -f build/$s/.sound ]&&echo Y||echo N) unsound=$([ -f build/$s/.unsound ]&&echo Y||echo N)" >> build/pipeline/blind_informed_batch.log
' _ {} &
wait
echo "PARALLEL-RECOVER-DONE $(date -u +%FT%TZ)" >> "$GL"
echo "PARALLEL-RECOVER-DONE" >> "$BL"
