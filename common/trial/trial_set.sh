#!/bin/bash
# trial_set.sh <slug-glob> <deepseek|mimo> [concurrency]
# Trial every SOUND task matching build/<glob> on ONE target model (3 runs, --full),
# <concurrency> at a time. Skips tasks already trialed on that target. Idempotent: safe to
# call repeatedly — it only picks up sound tasks not yet trialed on this target.
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
GLOB=${1:?slug-glob e.g. '*-ds'}; T=${2:?target deepseek|mimo}; C=${3:-6}
R="$CWE_ROOT"; cd "$R" || exit 1
# A task counts as trialed on $T only when trial_state.py says complete (solved, or 3 graded
# fails). Until 2026-10-20 any non-empty runs log counted, so one infra row (reward=None) or an
# older version's rows kept a task from ever being trialed. A trial already running is skipped.
# A task whose runs keep producing no result is "stuck": reported, not re-queued forever.
list=$(for m in build/$GLOB/.sound; do [ -e "$m" ] || continue; s=$(basename "$(dirname "$m")"); \
  st=$(python3 common/trial/trial_state.py "$s" "$T"); rc=$?; [ $rc -eq 0 ] && continue; \
  [ $rc -eq 3 ] && { echo "[trial_set] $s on $T STUCK ($st): not re-queued, needs a person" >&2; continue; }; \
  pgrep -f "[c]ommon/trial/trial\.py $s( |\$)" >/dev/null && continue; echo "$s"; done)
n=$(printf '%s\n' "$list" | grep -c . || true)
echo "[trial_set $(date -u +%T)] $GLOB on $T: $n task(s) to trial, C=$C"
[ "$n" = 0 ] && exit 0
# EARLY-ABORT (the user's rule): run 1, stop if solved; else run 2, 3. ~3x faster than --full on
# the common solved case, still 3 runs on a failure (needed to confirm a breaker). --no-verdict:
# we derive verdicts from runs_<target>.log, not queue.json.
printf '%s\n' "$list" | grep . | xargs -P "$C" -I '{}' python3 common/trial/trial.py '{}' --models "$T" --no-verdict >> build/pipeline/trials_$T.log 2>&1
echo "[trial_set $(date -u +%T)] $GLOB on $T: done"
