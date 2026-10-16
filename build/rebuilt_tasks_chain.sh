#!/usr/bin/env bash
# One-off chain (2026-10-15) for the five tasks rebuilt to keep hidden tests out of
# the image (hickory-dns, rclone, rclone-sib, russh, russh-sib):
#   1. full gate, one task at a time (one image build at a time; measured headroom
#      allows that alongside the live trials)
#   2. model runs for the task-model pairs with no clean verdict, each started only
#      after its task's gate PASSED and only when that model has a free slot
#      (at most 2 DeepSeek + 2 MiMo trials at once, counting trials started elsewhere)
#   3. when everything has finished: rebuild the results table and archive all runs
set -o pipefail   # no -u: bash 3.2 (macOS) treats empty arrays as unset
cd "$(dirname "$0")/.."
LOG=build/trial-logs/rebuilt_tasks_chain.log
say() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

running() {   # number of live trial.py jobs for a model (python processes only)
  pgrep -fl "build/trial.py [^ ]+ --models $1" | grep -v -e caffeinate -e zsh -e bash | wc -l | tr -d ' '
}
gate() {   # exit status 0 = gate passed
  say "gate $1: start"
  if python3 builder/gate.py "$1" >"build/trial-logs/gate_$1.log" 2>&1; then
    say "gate $1: PASSED"; return 0
  fi
  say "gate $1: FAILED -> $(tail -1 "build/trial-logs/gate_$1.log")"; return 1
}
PENDING=()          # "task:model" pairs waiting for a slot
launch_ready() {
  local keep=() p t m
  for p in ${PENDING[@]+"${PENDING[@]}"}; do
    t=${p%%:*}; m=${p##*:}
    if [ "$(running "$m")" -lt 2 ]; then
      python3 build/trial.py "$t" --models "$m" --no-verdict >"build/trial-logs/${t}__${m}-2h.log" 2>&1 &
      say "trial $t/$m: launched (pid $!)"; sleep 5
    else
      keep+=("$p")
    fi
  done
  PENDING=(${keep[@]+"${keep[@]}"})
}

gate hickory-dns && PENDING+=("hickory-dns:deepseek" "hickory-dns:mimo")
launch_ready
gate rclone && PENDING+=("rclone:mimo")
launch_ready
for t in rclone-sib russh russh-sib; do gate "$t"; launch_ready; done
say "all gates done; waiting for slots: ${PENDING[*]:-none}"

while [ ${#PENDING[@]} -gt 0 ]; do sleep 60; launch_ready; done
say "all queued trials launched; waiting for every trial to finish"
while pgrep -f "build/trial.py " >/dev/null; do sleep 60; done
say "all trials finished"

python3 build/audit_results.py >/dev/null && say "audit rebuilt: build/audit/ledger.md"
~/.local/share/uv/tools/harbor/bin/python -W ignore build/archive_runs.py >>"$LOG" 2>&1 \
  && say "archive updated" || say "ARCHIVE FAILED (see log)"
say "chain done"
