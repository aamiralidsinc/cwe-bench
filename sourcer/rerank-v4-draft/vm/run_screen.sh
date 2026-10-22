#!/bin/bash
# Run one screener-v1 prompt headless. Usage: run_screen.sh ROOT LABEL ENTRY_ID
#   LABEL claude-*            Claude Code, the VM's login, --model LABEL
#   LABEL deepseek-v4.1-flash Claude Code on DeepSeek's Anthropic endpoint (settings as harness/run_trial.sh)
#   LABEL mimo-v2.6-pro       Claude Code on MiMo's Anthropic endpoint (as harness/run_trial.sh)
#   LABEL gpt-*               Codex CLI, --model LABEL, reasoning effort xhigh (CODEX_EFFORT overrides)
# Claude Code runs: no shell, no web; file tools confined to the run dir and that host's code.
# Codex runs: workspace-write sandbox rooted at the run dir, no web search; its shell can read
# outside the run dir, so outputs of earlier waves are moved off this machine between waves.
# Keys for DeepSeek/MiMo: ~/.config/cwe/models.env (mode 600), never on the command line.
set -uo pipefail
ROOT=$1 LABEL=$2 EID=$3
RUN=$ROOT/runs/$LABEL/$EID
HOSTDIR=$ROOT/hosts/$EID
cd "$RUN" || exit 1
# Finished outputs go to $VAULT/<label>/<id>/. $VAULT is mode 0300 (no listing), so a run that
# searches the home directory cannot find another run's results; the copy-back opens it briefly.
VAULT=${VAULT:-$HOME/vault}
[ -s host.json ] || [ -s "$VAULT/$LABEL/$EID/host.json" ] && { echo "$LABEL $EID: already done"; exit 0; }
date -u +%FT%TZ > started.txt
PROMPT=$(cat prompt.md)
CC=("$HOME/.local/bin/claude" -p "$PROMPT" --restricted --safe-mode --strict-mcp-config
    --no-session-persistence --tools "Read,Grep,Glob,Write" --permission-mode acceptEdits
    --add-dir "$HOSTDIR" --output-format json)
case "$LABEL" in
  claude-*)
    timeout 1800 "${CC[@]}" --model "$LABEL" > run.json 2> run.err ;;
  deepseek-v4.1-flash|mimo-v2.6-pro)
    set -a; . "$HOME/.config/cwe/models.env"; set +a
    unset ANTHROPIC_AUTH_TOKEN CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_MODEL
    export API_TIMEOUT_MS=1200000
    if [ "$LABEL" = deepseek-v4.1-flash ]; then
      export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic ANTHROPIC_API_KEY=$DEEPSEEK_API_KEY
      export CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432 CLAUDE_CODE_MAX_OUTPUT_TOKENS=131072
      export CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1 MAX_THINKING_TOKENS=96000
      M=('deepseek-flash[1m]' --effort max)
    else
      export ANTHROPIC_BASE_URL=https://api.xiaomimimo.com/anthropic ANTHROPIC_API_KEY=$MIMO_API_KEY
      M=(mimo-v2.6-pro)
    fi
    unset DEEPSEEK_API_KEY MIMO_API_KEY
    timeout 1800 "${CC[@]}" --model "${M[@]}" > run.json 2> run.err ;;
  gpt-*)
    timeout 1800 "$HOME/.local/bin/codex" exec --model "${CODEX_MODEL:-$LABEL}" --sandbox workspace-write \
      --cd "$RUN" --skip-git-repo-check --ephemeral -c tools.web_search=false \
      -c model_reasoning_effort="${CODEX_EFFORT:-xhigh}" --json \
      -o last.txt "$PROMPT" > run.jsonl 2> run.err ;;
  *) echo "unknown label $LABEL" >&2; exit 2 ;;
esac
echo $? > exit.txt
date -u +%FT%TZ > finished.txt
had=$([ -s host.json ] && echo yes || echo NO)
mkdir -p "$VAULT/$LABEL/$EID"
mv -f host.json run.json run.jsonl run.err last.txt exit.txt started.txt finished.txt *.txt "$VAULT/$LABEL/$EID/" 2>/dev/null
find . -mindepth 1 ! -name prompt.md -exec mv -f -t "$VAULT/$LABEL/$EID/" {} + 2>/dev/null
echo "$LABEL $EID: exit $(cat "$VAULT/$LABEL/$EID/exit.txt"), host.json $had"
