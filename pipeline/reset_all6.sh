#!/bin/bash
# Reset the 6 fairfixed candidates to their pre-fairfix originals, preserving the fairfixed
# version first (for later fairfix-agent consistency comparison). litellm tasks/ already restored.
# Source of original = the trial-job postmortem evidence snapshot with the OLDEST instruction.md.
cd "$HOME/cwe-bench" || exit 1
PRES="$HOME/.tb-graders/cwe/work/fairfixed-preserve"
LOG=build/pipeline/reset_all6.log
mkdir -p "$PRES"
{
echo "=== reset_all6 $(date -u +%FT%TZ) ==="
for s in protobuf.js-ds airflow-ds hazelcast-ds electron-builder-credential-leakage vitest-api-fs-authz-inj; do
  echo "--- $s ---"
  # oldest evidence instruction.md = the original
  best=""; oldest=9999999999
  for e in $(ls -d ~/.tb-graders/cwe/jobs/${s}-*/*/postmortem-*/evidence 2>/dev/null); do
    [ -f "$e/instruction.md" ] || continue
    m=$(stat -c %Y "$e/instruction.md")
    if [ "$m" -lt "$oldest" ]; then oldest=$m; best=$e; fi
  done
  if [ -z "$best" ]; then echo "  NO evidence snapshot found -> SKIP (cannot reset cleanly)"; continue; fi
  echo "  source: $best (instr mtime $(date -u -d @$oldest +%m-%d:%H:%M))"
  echo "  pre-reset diff current-vs-original: $(diff tasks/$s/instruction.md "$best/instruction.md" 2>/dev/null | grep -c "^[<>]") lines"
  # preserve the fairfixed version
  rm -rf "$PRES/$s"; mkdir -p "$PRES/$s"
  cp -r tasks/$s "$PRES/$s/tasks" 2>/dev/null
  mkdir -p "$PRES/$s/build"; cp -r build/$s/checks build/$s/manifest.json build/$s/notes.md "$PRES/$s/build/" 2>/dev/null
  # restore tasks/ side from original
  cp "$best/instruction.md" tasks/$s/instruction.md
  [ -f "$best/task.toml" ] && cp "$best/task.toml" tasks/$s/task.toml
  rm -rf tasks/$s/tests && cp -r "$best/tests" tasks/$s/tests
  [ -f "$best/solution/fix.patch" ] && { mkdir -p tasks/$s/solution; cp "$best/solution/fix.patch" tasks/$s/solution/fix.patch; }
  echo "  POST-reset diff: $(diff tasks/$s/instruction.md "$best/instruction.md" 2>/dev/null | grep -c "^[<>]") lines (expect 0)"
  rm -f build/$s/fairfix-exit.txt
done
# litellm: tasks/ already restored earlier; just preserve+clear marker
[ -d "$PRES/litellm-ds" ] || { mkdir -p "$PRES/litellm-ds"; cp -r build/litellm-ds/.fairfixed-snapshot "$PRES/litellm-ds/" 2>/dev/null; }
rm -f build/litellm-ds/fairfix-exit.txt
echo "=== reset_all6 DONE $(date -u +%FT%TZ) ==="
echo "preserved fairfixed versions under: $PRES"
} >> "$LOG" 2>&1
cat build/pipeline/reset_all6.log
