#!/bin/bash
# Snapshot the CURRENT version of a task + its trial runs into a versioned experiment dir BEFORE an
# in-place edit (upgrade / fairfix / harden), so each version is a separate, traceable experiment.
#  - COPIES the task state (instruction.md, tests, solution, manifest, checks, notes, FAIRNESS, run
#    logs, gate reports) into the experiment dir; ORIGINALS stay in place for the editor to change.
#  - MOVES this version's trial run-folders out of the active jobs/ dir into the experiment dir, so
#    the next version's runs start clean and audit_results.py only ever sees current-version runs;
#    and REMOVES this version's result logs (runs_*.log, trial_detail*.json, trial outputs) from
#    build/<slug>/ once their copies are verified, so launchers never mix versions either.
#  - Writes PROVENANCE.json + appends to experiments/INDEX.tsv; bumps build/<slug>/VERSION.
set -uo pipefail
SLUG=${1:?usage: snapshot_experiment.sh SLUG}
R="$HOME/cwe-bench"; cd "$R" || exit 1
EXPROOT="$HOME/.tb-graders/cwe/experiments"
JOBS="$HOME/.tb-graders/cwe/jobs"
Vf="build/$SLUG/VERSION"
cur=$(cat "$Vf" 2>/dev/null || echo v1)
ts=$(date -u +%Y%m%dT%H%M%SZ)
dest="$EXPROOT/$SLUG/${cur}-$ts"
mkdir -p "$dest/task" "$dest/build" "$dest/runs"
cp -a "tasks/$SLUG/." "$dest/task/" 2>/dev/null || true
cp -a "build/$SLUG/." "$dest/build/" 2>/dev/null || true
# This version's RESULT files leave build/$SLUG with it (they are in $dest/build now). Left in
# place, the next version's launchers read the old rewards as their own: until 2026-10-20
# hubuum-client-rust-ds / flowise-ds were filed "SOLVED" on an older version's DeepSeek runs.
for f in "build/$SLUG"/runs_*.log "build/$SLUG"/trial_detail*.json "build/$SLUG"/auto_trial.out \
         "build/$SLUG"/trial_deepseek.out "build/$SLUG"/trial_mimo.out; do
  [ -f "$f" ] || continue
  if cmp -s "$f" "$dest/build/$(basename "$f")"; then rm -f "$f"
  else echo "snapshot: WARNING $f not copied intact to $dest/build; left in place" >&2; fi
done
# .auto_trialed said "THIS version was trialed"; the next version has not been (theia-ds v2 kept
# v1's marker and would never have been trialed). restore_snapshot.sh puts it back on a revert.
[ -f "$dest/build/.auto_trialed" ] && rm -f "build/$SLUG/.auto_trialed"
n=0
for jd in "$JOBS/$SLUG"-*; do
  [ -e "$jd" ] || continue
  case "$(basename "$jd")" in _*) continue;; esac   # skip archive dirs
  mv "$jd" "$dest/runs/" 2>/dev/null && n=$((n+1))
done
ish=$(sha256sum "tasks/$SLUG/instruction.md" 2>/dev/null | cut -c1-16)
cat > "$dest/PROVENANCE.json" <<JSON
{
  "slug": "$SLUG",
  "version": "$cur",
  "snapshot_utc": "$ts",
  "instruction_sha16": "$ish",
  "runs_archived": $n,
  "note": "task COPIED (originals left in place for the in-place edit); trial run-folders MOVED here out of jobs/ so the next version starts clean"
}
JSON
mkdir -p "$EXPROOT"
printf '%s\t%s\t%s\t%s\t%d\t%s\n' "$ts" "$SLUG" "$cur" "$ish" "$n" "$dest" >> "$EXPROOT/INDEX.tsv"
next="v$(( ${cur#v} + 1 ))"
echo "$next" > "$Vf"
# Where this snapshot went, so a failed edit can be undone (pipeline/restore_snapshot.sh).
printf '%s\n%s\n' "$dest" "$cur" > "build/$SLUG/.last_snapshot"
echo "snapshot: $SLUG $cur -> $dest (task copied, $n run-folders archived); new version=$next"
