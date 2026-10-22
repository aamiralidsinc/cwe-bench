#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/regate7_patched.log
SEVEN="fission-ds flowise-ds hermes-agent-ds limesurvey-ds pimcore-ds portainer-ds prompty-ds"
{
echo "=== re-gate 7 with harbor teardown-patch $(date -u +%FT%TZ) C=4 staggered ==="
printf "%s\n" $SEVEN | xargs -P4 -I{} bash -c "sleep \$((RANDOM % 20)); bash pipeline/gate_one_ds.sh \"\$1\"" _ {}
echo "--- verdicts ---"
for s in $SEVEN; do echo "  $s: $([ -f build/$s/.sound ] && echo SOUND || echo unsound)"; done
echo REGATE7-PATCHED-DONE
} >> "$LOG" 2>&1
