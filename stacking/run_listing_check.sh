#!/bin/bash
# Stacking listing check for one built stk- task (new; modelled on stacking/run_fairness_stack.sh).
# Read-only + Write, NO Docker/Bash in the agent. Classifies how instruction.md covers each hidden
# trap in manifest.traps (stacking/STACKING-LISTING-CHECK.md) and writes build/<slug>/listing.json.
# Launch through the driver (there is no default model):
#     ./drive.sh deepseek bash stacking/run_listing_check.sh SLUG
# Read the verdict ONLY with: python3 -I stacking/listing_verdict.py SLUG  (0 PASS, 1 FAIL, 2 ERROR)
# Exit 0 = a finished review; 1 = the agent did not finish (listing_status.txt says why; a previous
# listing.json is kept as listing.json.prev-<UTC>, never left looking current).
# A review that changed tasks/SLUG, build/SLUG/manifest.json or build/SLUG/checks/ is restored from a
# snapshot taken just before it and counts as not finished (2026-10-24).
set -uo pipefail
SLUG=${1:?usage: stacking/run_listing_check.sh SLUG}
R="$HOME/cwe-bench"; cd "$R" || exit 1
B=build/$SLUG
[ -n "${MODEL:-}" ] || { echo "error: MODEL not set; launch via ./drive.sh deepseek bash stacking/run_listing_check.sh $SLUG" | tee "$B/listing_status.txt"; exit 1; }
[ -f "tasks/$SLUG/instruction.md" ] && [ -f "$B/manifest.json" ] || { echo "error: no instruction.md or manifest.json" | tee "$B/listing_status.txt"; exit 1; }
P="$(sed -n "/^---8<---$/,\$p" stacking/STACKING-LISTING-CHECK.md | tail -n +2 | sed "s#{{ROOT}}#$R#g; s#{{SLUG}}#$SLUG#g")"
[ -f "$B/listing.json" ] && mv "$B/listing.json" "$B/listing.json.prev-$(date -u +%Y%m%dT%H%M%SZ)"
echo "running" > "$B/listing_status.txt"
# Integrity guard (2026-10-24): the reviewer has the Write tool over the whole project, so snapshot
# what it must not touch (the task tree, manifest.json, checks/) and restore it if anything changed.
fp() { find "tasks/$SLUG" "$B/manifest.json" "$B/checks" -type f 2>/dev/null | LC_ALL=C sort | xargs -r sha256sum | sha256sum | cut -d" " -f1; }
SNAP=$(mktemp -d); trap 'rm -rf "$SNAP"' EXIT
tar -cf "$SNAP/before.tar" "tasks/$SLUG" "$B/manifest.json" $( [ -d "$B/checks" ] && echo "$B/checks" )
before=$(fp)
timeout 1200 "$HOME/.local/bin/claude" -p "$P" --model "$MODEL" \
  --restricted --safe-mode --strict-mcp-config --no-session-persistence \
  --tools "Read,Grep,Glob,Write" --permission-mode acceptEdits --add-dir "$R" \
  --output-format json > "$B/listing-run.json" 2> "$B/listing-run.err"
rc=$?
st=$(python3 pipeline/agent_status.py "$B/listing-run.json" "$rc")
if [ "$(fp)" != "$before" ]; then
  rm -rf "tasks/$SLUG" "$B/checks"; tar -xf "$SNAP/before.tar"
  st="error: reviewer modified the task files (instruction, tests, manifest or checks); restored from the pre-review snapshot"
  [ "$(fp)" = "$before" ] || st="$st, BUT the restore did not match; inspect tasks/$SLUG by hand"
fi
if [ "$st" = ok ] && [ ! -s "$B/listing.json" ]; then st="error: agent finished but wrote no listing.json"; fi
if [ "$st" != ok ] && [ -f "$B/listing.json" ]; then mv "$B/listing.json" "$B/listing.json.unfinished-$(date -u +%Y%m%dT%H%M%SZ)"; fi
echo "$st" > "$B/listing_status.txt"
echo "$SLUG listing: $st; verdict: $(python3 -I stacking/listing_verdict.py "$SLUG" | head -1)"
[ "$st" = ok ]
