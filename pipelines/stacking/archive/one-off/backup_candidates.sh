#!/bin/bash
set -uo pipefail
cd "$HOME" || exit 1
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$HOME/stacking-candidates-backup-$STAMP.tar.zst"
CANDS="avideo-ghsaghcv filebrowser-ghsa8wc8 dagu-ghsaph8x mjml-ghsa45h5 siyuan-ghsa4mx9 tensorflow-ghsajjr8"
# Build the include list (relative to $HOME)
LIST=$(mktemp)
# all stacking task defs (tiny) + lightweight build records
ls -d cwe-bench/tasks/stk-* 2>/dev/null >> "$LIST"
ls -d cwe-bench/build/stk-* 2>/dev/null >> "$LIST"
echo "cwe-bench/build/pipeline/AUTO-STATE-TONIGHT.md" >> "$LIST"
# the 6 candidate tasks' full trial evidence + audit postmortems (incl both models, controls)
for c in $CANDS; do ls -d .tb-graders/cwe/jobs/stk-$c-* .tb-graders/cwe/jobs/stk-$c-control-* 2>/dev/null >> "$LIST"; done
echo "=== backing up $(grep -c . "$LIST") paths -> $OUT"
tar --zstd -cf "$OUT" \
  --exclude='*/harden_work' --exclude='*/exp' --exclude='*/.lockdir' \
  --exclude='*/node_modules' --exclude='*/target' --exclude='*/.git' \
  --exclude='*/.gradle' --exclude='*/.m2' \
  -T "$LIST" 2>/dev/null
rc=$?
rm -f "$LIST"
echo "=== tar rc=$rc size=$(du -sh "$OUT" 2>/dev/null | cut -f1)"
echo "=== verify: candidate audit verdicts present in the archive ==="
tar --zstd -tf "$OUT" 2>/dev/null | grep -c "verdict.json" | xargs echo "verdict.json files:"
tar --zstd -tf "$OUT" 2>/dev/null | grep -c "result.json" | xargs echo "result.json files:"
tar --zstd -tf "$OUT" 2>/dev/null | grep -c "tasks/stk-.*/instruction.md" | xargs echo "stk instruction.md:"
echo "DONE $OUT"
