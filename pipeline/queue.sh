#!/bin/bash
# queue.sh — run the CWE-bench pilot per pipeline/QUEUE.md, blocking between stages.
# Concurrency per activity = $C (default 6). Peak docker jobs kept ~2*C.
set -uo pipefail
R="$HOME/cwe-bench"; cd "$R" || exit 1
C=${C:-6}
QL="build/pipeline/queue.log"
log(){ echo "[queue $(date -u +%FT%TZ)] $*" | tee -a "$QL"; }
gone(){ ! ps -eo cmd | grep -qE "$1"; }                 # true when pattern absent
waitgone(){ while ! gone "$1"; do sleep 60; done; }

log "QUEUE START (C=$C)"

# ---- STAGE 1: DS builds complete ----
log "STAGE 1: wait for DS builds (run_lane deepseek + run_build *-ds) to finish"
waitgone "[r]un_lane.sh deepseek"
waitgone "[r]un_build.sh .*-ds"
log "STAGE 1b: regate false-unsound DS tasks"
bash pipeline/regate_unsound.sh deepseek >> "$QL" 2>&1 || true
log "DS builds done: sound=$(ls build/*-ds/.sound 2>/dev/null|wc -l) unsound=$(ls build/*-ds/.unsound 2>/dev/null|wc -l)"

# ---- STAGE 2: trial DS-tasks on DeepSeek ----
log "STAGE 2: trial DS-tasks on DeepSeek"
bash pipeline/trial_set.sh "*-ds" deepseek "$C" >> "$QL" 2>&1

# ---- STAGE 3: fairfix DS-tasks DeepSeek failed, re-trial on DeepSeek ----
log "STAGE 3: fairfix DeepSeek-failed DS-tasks (deepseek-driven)"
# A failed fairfix is not a fixed task, and a fixed task is re-gated before it is re-trialed
# (until 2026-10-20 both steps ran unchecked: `run_fairfix || true`, then a trial on whatever
# state the agent left). run_fairfix.sh snapshots the version, which moves the old runs log away.
for mk in build/*-ds/.sound; do [ -e "$mk" ] || continue; S=$(basename "$(dirname "$mk")")
  st=$(python3 pipeline/trial_state.py "$S" deepseek); case "$st" in failed*) ;; *) continue ;; esac
  log "  fairfix+retrial $S (DeepSeek: $st)"
  if ! ./drive.sh deepseek bash run_fairfix.sh "$S" >> "build/$S/pipeline.log" 2>&1; then
    log "  $S: fairfix did not finish cleanly ($(cat build/$S/fairfix_status.txt 2>/dev/null)); skipped, needs a person"
    continue
  fi
  if ! bash pipeline/gate_one_ds.sh "$S" >> "build/$S/pipeline.log" 2>&1; then
    log "  $S: not re-trialed, gate after fairfix: $(python3 -c "import json;d=json.load(open('build/$S/gate_verdict.json'));print(d['verdict'],d.get('stage'))" 2>/dev/null)"
    continue
  fi
  python3 build/trial.py "$S" --full --models deepseek >> "build/$S/trial_deepseek.out" 2>&1
  log "  $S re-trial: $(python3 pipeline/trial_state.py "$S" deepseek)"
done
log "DeepSeek phase COMPLETE. breakers-so-far scan:"; grep -rl . /dev/null 2>/dev/null || true

# ---- STAGE 4-6: MiMo phase ----
log "STAGE 4: prepare + launch MM builds (bg) and drain the trial matrix"
python3 -I pipeline/prepare_lane.py mimo >> "$QL" 2>&1
nohup bash pipeline/run_lane.sh mimo "$C" 50 >> build/pipeline/lane_mimo.log 2>&1 < /dev/null &
MMB=$!
log "MM build lane pid $MMB"
# Drain loop: trial every sound task not yet trialed on each target, until MM builds done
# AND every sound MM/DS task is trialed on both. trial_set calls are sequential (peak ~2C).
while :; do
  bash pipeline/trial_set.sh "*-ds" mimo "$C"      >> "$QL" 2>&1   # 4b: DS on MiMo
  bash pipeline/regate_unsound.sh mimo             >> "$QL" 2>&1 || true
  bash pipeline/trial_set.sh "*-mm" mimo "$C"      >> "$QL" 2>&1   # MM on MiMo
  bash pipeline/trial_set.sh "*-mm" deepseek "$C"  >> "$QL" 2>&1   # MM on DeepSeek
  if ! kill -0 "$MMB" 2>/dev/null; then
    rem=0
    for mk in build/*-ds/.sound build/*-mm/.sound; do [ -e "$mk" ] || continue; s=$(basename "$(dirname "$mk")")
      # done = complete (exit 0) or stuck (exit 3, reported by trial_set) on both models
      for t in deepseek mimo; do python3 pipeline/trial_state.py "$s" "$t" >/dev/null; case $? in 0|3) ;; *) rem=1 ;; esac; done; done
    [ "$rem" = 0 ] && break
  fi
  sleep 120
done
log "ALL STAGES COMPLETE $(date -u +%FT%TZ)"
log "FINAL: DS sound=$(ls build/*-ds/.sound 2>/dev/null|wc -l) MM sound=$(ls build/*-mm/.sound 2>/dev/null|wc -l)"
