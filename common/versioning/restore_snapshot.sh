#!/bin/bash
# restore_snapshot.sh SLUG "<why>" : undo the in-place edit that followed the latest
# snapshot_experiment.sh, after the editing agent (harden / fairfix / upgrade) failed or changed
# nothing. Puts back the task tree, the gate inputs (manifest, checks, notes), the version, the
# result logs and the trial run-folders, so the task is exactly the version that was trialed.
# Without this a quota-cut agent left a half-edited task still marked .sound, and the trial
# folders of the real current version were hidden from audit_results.py in the experiment dir.
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
. "$CWE_COMMON/markers.sh"     # marker helpers (common/markers.py, docs/STAGE-CONTRACTS.md)
SLUG=${1:?usage: restore_snapshot.sh SLUG "<why>"}; WHY=${2:-unspecified}
cd "$CWE_ROOT" || exit 1
B=build/$SLUG; JOBS="$HOME/.tb-graders/cwe/jobs"
[ -f "$B/.last_snapshot" ] || { echo "restore: $SLUG has no .last_snapshot; nothing restored" >&2; exit 1; }
dest=$(sed -n 1p "$B/.last_snapshot"); ver=$(sed -n 2p "$B/.last_snapshot")
[ -d "$dest/task" ] && [ -d "$dest/build" ] || { echo "restore: $dest is incomplete; nothing restored" >&2; exit 1; }
[ -f "$dest/REVERTED.txt" ] && { echo "restore: $dest was already restored" >&2; exit 0; }
# The task tree, exactly as snapshotted (files the agent added are removed).
rm -rf "tasks/$SLUG.restore-tmp" && cp -a "$dest/task" "tasks/$SLUG.restore-tmp" \
  && rm -rf "tasks/$SLUG" && mv "tasks/$SLUG.restore-tmp" "tasks/$SLUG" \
  || { echo "restore: could not restore tasks/$SLUG" >&2; exit 1; }
# Gate inputs and this version's results; logs of the failed edit itself stay for diagnosis.
rm -rf "$B/checks"; [ -d "$dest/build/checks" ] && cp -a "$dest/build/checks" "$B/checks"
for f in manifest.json notes.md FAIRNESS.md VERSION .sound .unsound .gate_error .auto_trialed \
         runs_deepseek.log runs_mimo.log trial_detail.json trial_detail_deepseek.json \
         trial_detail_mimo.json auto_trial.out trial_deepseek.out trial_mimo.out; do
  cwe_unmark "$B" "$f"; [ -e "$dest/build/$f" ] && cp -a "$dest/build/$f" "$B/$f"
done
echo "$ver" > "$B/VERSION"
n=0
for jd in "$dest/runs"/*; do [ -e "$jd" ] || continue; mv "$jd" "$JOBS/" && n=$((n+1)); done
echo "restored $(date -u +%FT%TZ): $WHY; $n run-folder(s) returned to jobs/" > "$dest/REVERTED.txt"
rm -f "$B/.last_snapshot"
echo "restore: $SLUG back to $ver ($WHY); $n run-folder(s) returned"
