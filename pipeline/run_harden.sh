#!/bin/bash
# Harden one fair-but-solved task: PRE-verdict (can it be hardened?), if yes harden + convert to the
# Frontier delivery format, POST-verdict (fail confidence). The agent writes build/<slug>/harden_verdict.json.
# Usage: ./drive.sh deepseek bash pipeline/run_harden.sh SLUG   (MODEL is required; drive.sh sets it)
# Exit: 0 = hardened (can_harden=true, changed)  -> caller re-gates and, if SOUND, re-trials
#       1 = the agent did not finish / no valid verdict          -> restore; not a round
#       3 = can_harden=true but the agent changed nothing (bug)  -> restore; not a round
#       4 = can_harden=false (no fair lever)                     -> REMOVE the task (drop; stays solvable)
set -uo pipefail
SLUG=${1:?usage: run_harden.sh SLUG}
cd "$HOME/cwe-bench" || exit 1
B=build/$SLUG
[ -n "${MODEL:-}" ] || { echo "error: MODEL not set; launch via ./drive.sh deepseek bash pipeline/run_harden.sh $SLUG" | tee "$B/harden_status.txt"; exit 1; }
echo "running" > "$B/harden_status.txt"
rm -f "$B/harden_verdict.json"
mkdir -p "$HOME/.tb-graders/cwe/work/$SLUG"
# Per-trap, per-model results of this version's runs, for the agent (build/$SLUG/trial_summary.md).
# Written BEFORE the snapshot, which moves the runs out of jobs/. Never fails the launch.
python3 -I pipeline/trial_summary.py "$SLUG" || true
bash pipeline/snapshot_experiment.sh "$SLUG"  # preserve prior version before in-place edit (provenance)
fp() { find "tasks/$SLUG" "$B/checks" "$B/manifest.json" -type f 2>/dev/null | sort | xargs cat 2>/dev/null | sha256sum | cut -d' ' -f1; }
PRE=$(fp)
P=$(sed "s/{{SLUG}}/$SLUG/g" builder/HARDENING-PROMPT.md)
date -u +%FT%TZ > "$B/harden_start.txt"
timeout "${HARDEN_TIMEOUT:-10800}" "$HOME/.local/bin/claude" -p "$P" --model "$MODEL" \
  --permission-mode bypassPermissions --add-dir "$HOME/cwe-bench" --add-dir "$HOME/.tb-graders/cwe/work" \
  --output-format json > "$B/harden-run.json" 2> "$B/harden-run.err"
rc=$?
echo $rc > "$B/harden-exit.txt"
st=$(python3 pipeline/agent_status.py "$B/harden-run.json" "$rc" --details "$B/harden_status.json")

# The agent must leave a valid harden_verdict.json. Parse it to decide the outcome.
verdict=$(python3 - "$B/harden_verdict.json" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    ch = d.get("can_harden")
    if ch is True:  print("can_harden")
    elif ch is False: print("cannot")
    else: print("invalid")
except Exception:
    print("missing")
PY
)

code=0
if [ "$st" != ok ]; then
  code=1                                   # agent did not finish cleanly
elif [ "$verdict" = "missing" ] || [ "$verdict" = "invalid" ]; then
  st="finished but wrote no valid harden_verdict.json"; code=1
elif [ "$verdict" = "cannot" ]; then
  reason=$(python3 -c "import json;print(json.load(open('$B/harden_verdict.json')).get('reason',''))" 2>/dev/null)
  st="can_harden=false: $reason"; code=4   # remove the task
elif [ "$(fp)" = "$PRE" ]; then
  st="can_harden=true but the agent changed no task file"; code=3
fi
echo "$st" > "$B/harden_status.txt"
echo "$SLUG harden: exit $rc; verdict=$verdict; $st"
# Restore the task exactly as trialed when it is NOT a hardening round and NOT a clean remove.
case $code in
  1|3) bash pipeline/restore_snapshot.sh "$SLUG" "harden: $st" ;;
esac
exit $code
