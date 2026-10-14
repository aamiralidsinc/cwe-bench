#!/usr/bin/env bash
# Run a Harbor task with Claude Code driving DeepSeek V4.1 Flash or MiMo-V2.6-Pro.
#
#   run_trial.sh <deepseek|mimo> <task-dir> [attempts] [extra harbor args...]
#
# Keys (DEEPSEEK_API_KEY, MIMO_API_KEY) are read from an env file, see below.
# Harbor installs Claude Code into the task container itself, so no task image
# needs changing: the model is selected entirely by the settings below.
set -euo pipefail

model=${1:?usage: run_trial.sh <deepseek|mimo> <task-dir> [attempts] [harbor args...]}
task=${2:?task directory required}
attempts=${3:-1}
shift $(( $# < 3 ? $# : 3 ))

# First file found wins: $CWE_MODELS_ENV, ~/.tb-graders/cwe/models.env, then the
# repo's git-ignored .env.
here=$(cd "$(dirname "$0")" && pwd)
for env_file in "${CWE_MODELS_ENV:-}" "$HOME/.tb-graders/cwe/models.env" "$here/../../.env"; do
  if [ -n "$env_file" ] && [ -f "$env_file" ]; then set -a; . "$env_file"; set +a; break; fi
done

extra=()
case "$model" in
  deepseek)
    # https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/
    base_url=https://api.deepseek.com/anthropic
    key=${DEEPSEEK_API_KEY:?DEEPSEEK_API_KEY is not set (see models.env.example)}
    model_id='deepseek-flash[1m]'   # served by DeepSeek-V4.1-Flash, 1M context
    effort=${EFFORT-max}
    extra+=(--ae CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432)
    ;;
  mimo)
    base_url=https://api.xiaomimimo.com/anthropic
    key=${MIMO_API_KEY:?MIMO_API_KEY is not set (see models.env.example)}
    model_id=mimo-v2.6-pro
    effort=${EFFORT-}
    ;;
  *) echo "unknown model: $model (expected deepseek or mimo)" >&2; exit 2 ;;
esac
[ -n "$effort" ] && extra+=(--ak "reasoning_effort=$effort")

# Passed through the process environment, not --ae, so the key stays out of
# the command line and the job's saved config.
export ANTHROPIC_BASE_URL=$base_url ANTHROPIC_API_KEY=$key
unset ANTHROPIC_AUTH_TOKEN CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_MODEL

exec harbor run -p "$task" -a claude-code -m "$model_id" -k "$attempts" \
  -o "${JOBS_DIR:-$HOME/.tb-graders/cwe/jobs}" \
  --job-name "$(basename "$task")-$model-$(date +%m%d-%H%M%S)" \
  ${extra[@]+"${extra[@]}"} "$@"
