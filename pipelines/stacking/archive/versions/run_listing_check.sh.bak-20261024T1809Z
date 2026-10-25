#!/bin/bash
# Stacking listing check for one built stk- task (new; modelled on stacking/run_fairness_stack.sh).
# Read-only + Write, NO Docker/Bash in the agent. Classifies how instruction.md covers each hidden
# trap in manifest.traps (stacking/STACKING-LISTING-CHECK.md) and writes build/<slug>/listing.json.
# Launch through the driver (there is no default model):
#     ./drive.sh deepseek bash stacking/run_listing_check.sh SLUG
# Read the verdict ONLY with: python3 -I stacking/listing_verdict.py SLUG  (0 PASS, 1 FAIL, 2 ERROR)
# Exit 0 = a finished review; 1 = the agent did not finish (listing_status.txt says why; a previous
# listing.json is kept as listing.json.prev-<UTC>, never left looking current).
set -uo pipefail
SLUG=${1:?usage: stacking/run_listing_check.sh SLUG}
R="$HOME/cwe-bench"; cd "$R" || exit 1
B=build/$SLUG
[ -n "${MODEL:-}" ] || { echo "error: MODEL not set; launch via ./drive.sh deepseek bash stacking/run_listing_check.sh $SLUG" | tee "$B/listing_status.txt"; exit 1; }
[ -f "tasks/$SLUG/instruction.md" ] && [ -f "$B/manifest.json" ] || { echo "error: no instruction.md or manifest.json" | tee "$B/listing_status.txt"; exit 1; }
P="$(sed -n "/^---8<---$/,\$p" stacking/STACKING-LISTING-CHECK.md | tail -n +2 | sed "s#{{ROOT}}#$R#g; s#{{SLUG}}#$SLUG#g")"
[ -f "$B/listing.json" ] && mv "$B/listing.json" "$B/listing.json.prev-$(date -u +%Y%m%dT%H%M%SZ)"
echo "running" > "$B/listing_status.txt"
timeout 1200 "$HOME/.local/bin/claude" -p "$P" --model "$MODEL" \
  --restricted --safe-mode --strict-mcp-config --no-session-persistence \
  --tools "Read,Grep,Glob,Write" --permission-mode acceptEdits --add-dir "$R" \
  --output-format json > "$B/listing-run.json" 2> "$B/listing-run.err"
rc=$?
st=$(python3 pipeline/agent_status.py "$B/listing-run.json" "$rc")
if [ "$st" = ok ] && [ ! -s "$B/listing.json" ]; then st="error: agent finished but wrote no listing.json"; fi
if [ "$st" != ok ] && [ -f "$B/listing.json" ]; then mv "$B/listing.json" "$B/listing.json.unfinished-$(date -u +%Y%m%dT%H%M%SZ)"; fi
echo "$st" > "$B/listing_status.txt"
echo "$SLUG listing: $st; verdict: $(python3 -I stacking/listing_verdict.py "$SLUG" | head -1)"
[ "$st" = ok ]
