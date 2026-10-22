#!/bin/bash
# Retrial stage for the 7 fairfixed tasks (all RETRIAL; 0 regrade).
# 1) archive pre-fairfix runs (task changed); 2) re-gate the 3 non-sound;
# 3) DeepSeek retrials now for the 4 sound (early-abort). MiMo deferred until litellm r4 frees MiMo.
cd "$HOME/cwe-bench" || exit 1
LOG=build/pipeline/retrial_stage.log
ARCH="$HOME/.tb-graders/cwe/jobs/_pre-fairfix-archive"
mkdir -p "$ARCH"
export DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 COMPOSE_HTTP_TIMEOUT=300 DOCKER_CLIENT_TIMEOUT=300
SOUND="protobuf.js-ds airflow-ds hazelcast-ds hermes-agent-ds"
NONSOUND="prompty-path-read-inj flowise-cross-tenant-inj vitest-api-fs-authz-inj"
{
echo "=== retrial_stage START $(date -u +%FT%TZ) ==="
for s in $SOUND $NONSOUND; do
  n=0; for jd in $(ls -d ~/.tb-graders/cwe/jobs/${s}-* 2>/dev/null); do mv "$jd" "$ARCH/" 2>/dev/null && n=$((n+1)); done
  echo "  archived $n pre-fairfix run-folders for $s"
done
echo "re-gating 3 non-sound (P2): $NONSOUND"
printf '%s\n' $NONSOUND | xargs -P2 -I{} bash pipeline/gate_one_ds.sh {} >> "$LOG" 2>&1
for s in $NONSOUND; do echo "  $s: $([ -f build/$s/.sound ]&&echo SOUND||echo unsound)"; done
echo "DeepSeek retrials now (4 sound, early-abort, P2): $SOUND"
printf '%s\n' $SOUND | xargs -P2 -I{} bash -c 'cd "$HOME/cwe-bench"; python3 build/trial.py "$1" --models deepseek >> "build/$1/retrial.nohup" 2>&1; echo "[ds-retrial $1] $(grep -oE reward=[0-9.]+ build/$1/runs_deepseek.log 2>/dev/null|paste -sd, -)" >> build/pipeline/retrial_stage.log' _ {}
echo "=== retrial_stage DS phase DONE $(date -u +%FT%TZ) (MiMo retrials pending litellm r4) ==="
echo ALL-RETRIAL-DS-DONE
} >> "$LOG" 2>&1
