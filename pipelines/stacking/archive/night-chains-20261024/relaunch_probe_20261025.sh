#!/bin/bash
# Relaunch trial pairs whose every start was refused by harbor's 30 s kernel probe (patched to 300 s).
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/relaunch_probe.log
log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
go() { log "launch $*"; setsid nohup env $ENVV python3 build/trial.py "$@" --no-verdict > "build/$1/trial_relaunch_$(date +%H%M%S).log" 2>&1 < /dev/null & sleep $((60 + RANDOM % 31)); }
ENVV="CWE_AGENT_TIMEOUT_MULT=1.5" go stk-tensorflow-ghsajjr8 --models mimo --first-run 4 --max-runs 4
ENVV="X=1"
go stk-langflow-794-control --models deepseek --first-run 1 --max-runs 3
go stk-langflow-794-control --models mimo --first-run 1 --max-runs 3
go stk-senaite-core-4280-control --models deepseek --first-run 1 --max-runs 3
go stk-senaite-core-4280-control --models mimo --first-run 1 --max-runs 3
go stk-vikunja-ghsaxv7q --models deepseek --first-run 1 --max-runs 3
go stk-vikunja-ghsaxv7q --models mimo --first-run 1 --max-runs 3
go stk-openbao-ghsac36x-control --models deepseek --first-run 1 --max-runs 3
log "all launched"
