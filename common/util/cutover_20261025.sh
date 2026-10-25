#!/bin/bash
# One-time switch of the VM working tree to the reorganised repo (2026-10-25). Run ON THE VM, only when idle:
#   bash ~/cwe-bench-staging/common/util/cutover_20261025.sh <path-to-git-source> [--go]
# <path-to-git-source> is a git bundle or URL holding branch reorg-20261025 (or main after it is merged).
# Without --go it only checks (idle check + plan) and changes nothing.
#
# What it does, in order (aborts on the first failure, before anything moves):
#   1. refuses if anything pipeline-related is running (trials, harbor, gates, agents, queues, lanes, chains);
#   2. records the outputs of the read-only tools on the OLD tree (for a before/after comparison);
#   3. backs up the old code (no build/ or tasks/ data) to ~/backups/;
#   4. renames ~/cwe-bench -> ~/cwe-bench-legacy-20261025 (same filesystem: instant, nothing copied);
#   5. clones the new repo to a temporary folder FIRST, then swaps it in and MOVES build/ and tasks/ into it;
#   6. merges the VM-only run records: legacy stacking/out -> pipelines/stacking/out and sibling2/out ->
#      pipelines/sibling/out (the VM copy wins, except three newer Mac selection outputs; night chains not copied);
#   7. re-runs the read-only tools on the NEW tree and compares with step 2 (must be identical);
#   8. checks the harbor patches and makes the legacy code read-only.
# Rollback (before anything new has run): rm -rf ~/cwe-bench && mv ~/cwe-bench-legacy-20261025 ~/cwe-bench,
# after moving build/ and tasks/ back into it.
set -euo pipefail
SRC=${1:?usage: cutover_20261025.sh <git-bundle-or-url> [--go]}; GO=${2:-}
# CWE_CUTOVER_OLD lets you rehearse on a copy of the tree; the default is the real ~/cwe-bench.
OLD=${CWE_CUTOVER_OLD:-$HOME/cwe-bench}; LEG=$OLD-legacy-20261025; TS=$(date -u +%Y%m%dT%H%M%SZ)
W=$HOME/backups/cutover-$TS; mkdir -p "$W"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$W/cutover.log"; }

# 1. idle check
busy_list() {
  local p a
  for p in /proc/[0-9]*; do
    a=$( { tr '\0' ' ' < "$p/cmdline"; } 2>/dev/null ) || continue
    case "$a" in
      *"build/trial.py"*|*"common/trial/trial.py"*|*"harbor run"*|*"gate.py"*|*"gate_one_ds.sh"*|*"run_build.sh"*|\
      *"run_fairfix"*|*"run_fairness"*|*"run_upgrade"*|*"run_blindfix"*|*"run_listing_check"*|*"stk_queue.py"*|\
      *"run_stack_pipeline"*|*"ramp_lane"*|*"run_lane"*|*"run_pipeline.sh"*|*"_chain_"*|*"claude -p"*)
        echo "${p#/proc/} ${a:0:120}" ;;
    esac
  done
}
busy=$(busy_list)
[ -z "$busy" ] || { say "NOT IDLE, refusing:"; echo "$busy" | tee -a "$W/cutover.log"; exit 2; }
[ -d "$OLD/build" ] && [ -d "$OLD/stacking" ] || { say "$OLD does not look like the old layout; refusing"; exit 2; }
[ ! -e "$LEG" ] || { say "$LEG already exists; refusing"; exit 2; }
say "idle; source $SRC; plan: rename $OLD -> $LEG, clone new, move build/ tasks/, merge out/ records"
[ "$GO" = "--go" ] || { say "dry run only (pass --go to switch)"; exit 0; }

# 2. old-tree outputs (the read-only tools return non-zero codes by design: stuck, NOT_READY, FAIL;
#    the subshells run without errexit so those codes are recorded, not fatal)
SL=$(cd "$OLD" && for d in build/stk-*/; do basename "$d"; done | grep -v -- -control | awk "NR<=12")
oldrun() { (set +e +o pipefail; cd "$OLD" && for s in $SL; do for m in deepseek mimo; do python3 -I pipeline/trial_state.py "$s" "$m"; done
  python3 pipeline/fairness_verdict.py "$s"; python3 -I stacking/listing_verdict.py "$s" | sed -n 1p; done
  python3 -I stacking/stk_queue.py trial --dry-run | sed 's#build/trial.py#TRIAL#') 2>&1; }
newrun() { (set +e +o pipefail; cd "$OLD" && for s in $SL; do for m in deepseek mimo; do python3 -I common/trial/trial_state.py "$s" "$m"; done
  python3 common/fairness/fairness_verdict.py "$s"; python3 -I pipelines/stacking/4-listing/listing_verdict.py "$s" | sed -n 1p; done
  python3 -I pipelines/stacking/6-trial/stk_queue.py trial --dry-run | sed "s#$OLD/common/trial/trial.py#TRIAL#") 2>&1; }
oldrun > "$W/tools-before.txt"; say "recorded old-tree tool outputs ($(wc -l < "$W/tools-before.txt") lines)"

# 3. code backup
tar --exclude="$(basename "$OLD")/build/*/" --exclude='*/__pycache__' -czf "$HOME/backups/cwe-bench-legacy-code-$TS.tgz" -C "$(dirname "$OLD")" \
  $(cd "$(dirname "$OLD")" && B=$(basename "$OLD"); ls -d $B/builder $B/pipeline $B/harness $B/stacking $B/sibling2 $B/sourcer $B/*.sh $B/*.sh.bak-* 2>/dev/null; find $B/build -maxdepth 1 -type f)
chmod 444 "$HOME/backups/cwe-bench-legacy-code-$TS.tgz"; say "code backup: ~/backups/cwe-bench-legacy-code-$TS.tgz"

# 4-5. switch: clone FIRST (abort before touching the old tree if that fails), then swap, then move run data
NEWTMP=$OLD-new-$TS
git clone -q -b reorg-20261025 "$SRC" "$NEWTMP" || git clone -q "$SRC" "$NEWTMP"
[ -f "$NEWTMP/.cwe-bench-root" ] || { say "clone has no .cwe-bench-root; refusing (old tree untouched)"; exit 2; }
(cd "$NEWTMP" && git config user.name "Mara Hassan" && git config user.email "mara.hassann@gmail.com")
rm -rf "$NEWTMP/build" "$NEWTMP/tasks"
trap 'say "FAILED after the swap began. Rollback: move build/ and tasks/ back into $LEG if needed, rm -rf $OLD, mv $LEG $OLD"' ERR
mv "$OLD" "$LEG"; mv "$NEWTMP" "$OLD"; say "renamed old tree to $LEG; new tree in place"
mv "$LEG/build" "$OLD/build"; mv "$LEG/tasks" "$OLD/tasks"; say "moved build/ and tasks/ into the new tree"
# build/ moved whole, so its top level still holds the OLD tool scripts and docs (now in common/audit, common/trial,
# attic/, docs/history/). Move them into the legacy tree so nobody can run an old build/trial.py by mistake.
# (build/queue.json is NOT moved: it is trial.py's live verdict state. The 2026-10-25 run moved it by mistake and
# it was restored from the legacy tree the same day.)
mkdir -p "$LEG/build-toplevel-old-tools"
for f in "$OLD"/build/*.py "$OLD"/build/*.py.bak* "$OLD"/build/*.sh \
         "$OLD"/build/RESULTS-AUDIT.md "$OLD"/build/RESUME-2026-10-17.md "$OLD"/build/TRIAL-PROCEDURE.md "$OLD"/build/trial-matrix.md; do
  [ -f "$f" ] && mv "$f" "$LEG/build-toplevel-old-tools/"
done
rm -rf "$OLD/build/__pycache__"
say "moved the old build/ top-level tools to $LEG/build-toplevel-old-tools/ ($(ls "$LEG/build-toplevel-old-tools" | wc -l) files)"

# 6. run records: the VM's copies win (they are the live records); except three selection outputs whose Mac copy,
#    already in the repo, is newer (out/screener/, out/h4_candidates.tsv, out/h4_shortlist.md). The night-chain scripts
#    were archived and are not copied back.
rsync -a --exclude='*_2026102[0-9].sh' --exclude='__pycache__/' --exclude='._*' \
  --exclude='/screener/' --exclude='/h4_candidates.tsv' --exclude='/h4_shortlist.md' "$LEG/stacking/out/" "$OLD/pipelines/stacking/out/"
rsync -a --exclude='__pycache__/' --exclude='._*' "$LEG/sibling2/out/" "$OLD/pipelines/sibling/out/"
say "merged run records into pipelines/*/out/"
trap - ERR

# 7. compare
newrun > "$W/tools-after.txt"
if cmp -s "$W/tools-before.txt" "$W/tools-after.txt"; then say "tool outputs IDENTICAL before/after"
else say "TOOL OUTPUTS DIFFER: see diff below (the switch is done; investigate before running anything)"; ( diff "$W/tools-before.txt" "$W/tools-after.txt" | sed -n 1,40p | tee -a "$W/cutover.log" ) || true; fi

# 8. harbor patches + legacy read-only
bash "$OLD/common/trial/harbor/patch_probe_timeout.sh" | tee -a "$W/cutover.log"
D=$HOME/.local/share/uv/tools/harbor/lib/python3.13/site-packages/harbor/environments/docker/docker.py
grep -q 'if "down" in full_command' "$D" && say "harbor patch A present" || say "WARNING: harbor patch A missing: run common/trial/harbor/patch_teardown.sh (harbor part)"
chmod -R a-w "$LEG"; say "legacy tree is read-only: $LEG"
say "DONE. New tree: $OLD ($(cd "$OLD" && git log -1 --format='%h %s' | cut -c1-60))"
