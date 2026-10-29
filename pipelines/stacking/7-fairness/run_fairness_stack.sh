#!/bin/bash
# STACKING COPY of pipelines/sibling/9-fairness/run_fairness.sh (original untouched). Differences: appends
# pipelines/stacking/7-fairness/STACKING-FAIRNESS-ADDENDUM.md to the brief; project root from $HOME. Use for stk-* tasks.
# Fairness review for one built task (gate prerequisite). Read-only + Write, NO Docker/Bash in the
# agent, so it is safe to run like the screener. Writes build/<slug>/FAIRNESS.md.
# Launch through the driver (there is no default model): common/launch/drive.sh deepseek bash pipelines/stacking/7-fairness/run_fairness_stack.sh SLUG
# Read the verdict ONLY with common/fairness/fairness_verdict.py (last GATE_A line; ERROR if this run failed).
# Exit 0 = a finished review; 1 = the agent did not finish (fairness_status.txt says why; the
# previous FAIRNESS.md is kept as FAIRNESS.md.prev-<UTC>, never left looking current).
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
SLUG=${1:?usage: pipelines/stacking/7-fairness/run_fairness_stack.sh SLUG}
cd "$CWE_ROOT" || exit 1
B=build/$SLUG
[ -n "${MODEL:-}" ] || { echo "error: MODEL not set; launch via common/launch/drive.sh deepseek bash pipelines/stacking/7-fairness/run_fairness_stack.sh $SLUG" | tee "$B/fairness_status.txt"; exit 1; }
BRIEF="$(cat "$CWE_FAIRNESS_BRIEF")

$(sed -n "/^---8<---$/,\$p" pipelines/stacking/7-fairness/STACKING-FAIRNESS-ADDENDUM.md | tail -n +2)"
P="$BRIEF

Review SLUG=$SLUG. The project root here is $CWE_ROOT (NOT the path in the brief): read tasks/$SLUG/instruction.md, tasks/$SLUG/tests/, tasks/$SLUG/solution/fix.patch, build/$SLUG/manifest.json, build/$SLUG/notes.for-review.md (the build notes without earlier conclusions; never open build/$SLUG/notes.md, build/$SLUG/history/, FAIRNESS.md.prev-*, HUMAN-DECISION.md or any audit or postmortem file), build/$SLUG/checks/*.patch, build/$SLUG/gate_report.json, build/$SLUG/trial_summary.md (if present); write build/$SLUG/FAIRNESS.md. Do not run anything."
# The failing tests of each run, for the brief's "deciding" column (step 1a); never fails the review.
python3 -I "$CWE_TRIAL_SUMMARY" "$SLUG" > /dev/null 2>&1 || true
# The reviewer judges on its own: it reads the build notes without earlier conclusions (audit, fairness, decision and
# run outcomes; common/util/notes_filter.py). If the filter fails it gets no notes, never the raw ones.
python3 -I "$CWE_COMMON/util/notes_filter.py" "$B/notes.md" "$B/notes.for-review.md" > /dev/null 2>&1 \
  || echo "(build notes unavailable)" > "$B/notes.for-review.md"
# A stale review must never pass for this run's result.
[ -f "$B/FAIRNESS.md" ] && mv "$B/FAIRNESS.md" "$B/FAIRNESS.md.prev-$(date -u +%Y%m%dT%H%M%SZ)"
echo "running" > "$B/fairness_status.txt"
date -u +%FT%TZ > "$B/fairness_start.txt"
timeout 2400 "$HOME/.local/bin/claude" -p "$P" --model "$MODEL" \
  --restricted --safe-mode --strict-mcp-config --no-session-persistence \
  --tools "Read,Grep,Glob,Write" --permission-mode acceptEdits --add-dir "$CWE_ROOT" --add-dir "$CWE_DATA_ROOT" \
  --output-format json > "$B/fairness-run.json" 2> "$B/fairness-run.err"
rc=$?
st=$(python3 "$CWE_AGENT_STATUS" "$B/fairness-run.json" "$rc" --details "$B/fairness_status.json")
if [ "$st" = ok ] && [ ! -s "$B/FAIRNESS.md" ]; then st="error: agent finished but wrote no FAIRNESS.md"; fi
if [ "$st" != ok ] && [ -f "$B/FAIRNESS.md" ]; then mv "$B/FAIRNESS.md" "$B/FAIRNESS.md.unfinished-$(date -u +%Y%m%dT%H%M%SZ)"; fi
echo "$st" > "$B/fairness_status.txt"
echo "$SLUG fairness: $st; verdict: $(python3 "$CWE_FAIRNESS_VERDICT" "$SLUG")"
[ "$st" = ok ]
