#!/bin/bash
# Advance ONE failed candidate through fairness/fairfix (DeepSeek, no Docker, NO trial).
# none -> run fairness. NOT-READY -> fairfix then re-fairness, up to 2 rounds (cap). READY -> stop.
# ERROR (no review, no GATE_A line, or a fairness/fairfix run that did not finish) -> stop and
# flag for a person; never treated as READY or NOT READY (common/fairness/fairness_verdict.py).
# Trials are deferred until the gate phase drains (scheduler barrier). Detached-safe.
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
cd "$CWE_ROOT" || exit 1
s=$1
L="build/pipeline/advance_${s}.log"
fv() { python3 "$CWE_FAIRNESS_VERDICT" "$s"; }
{
echo "=== advance $s START $(date -u +%FT%TZ) ==="
if [ ! -f "build/$s/FAIRNESS.md" ]; then
  echo "[fairness-initial]"; "$CWE_DRIVE" deepseek bash pipelines/sibling/9-fairness/run_fairness.sh "$s"
fi
for r in 1 2; do
  v=$(fv)
  case "$v" in
    READY*)     echo "[r$r] $v -> stop"; break ;;
    NOT_READY*) ;;
    *)         echo "[r$r] $v -> stop, needs a person"; break ;;
  esac
  echo "[r$r] fairfix"
  if ! "$CWE_DRIVE" deepseek bash pipelines/sibling/10-fairfix/run_fairfix.sh "$s"; then
    echo "[r$r] fairfix did not finish ($(cat build/$s/fairfix_status.txt 2>/dev/null)); task restored -> stop"; break
  fi
  echo "[r$r] re-fairness"; "$CWE_DRIVE" deepseek bash pipelines/sibling/9-fairness/run_fairness.sh "$s"
done
echo "=== advance $s DONE $(date -u +%FT%TZ) fairness=$(fv) ==="
} >> "$L" 2>&1
