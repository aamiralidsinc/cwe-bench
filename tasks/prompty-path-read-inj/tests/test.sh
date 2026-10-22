#!/bin/bash
# Verifier entry point. Runs the hidden tests against whatever is in /app and
# writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Never trust test files inside /app: the agent could have edited them. Run
# only the copies under /tests.

# Stop the agent before grading. On an agent timeout Harbor stops waiting for the agent but
# does not kill it inside this shared container; in round 1 it kept editing /app while the
# tests ran (15 runs). Kill every Claude Code process first. Do not remove this block.
for _p in /proc/[0-9]*; do
  case "$(tr '\0' ' ' < "$_p/cmdline" 2>/dev/null)" in
    claude\ *|*/claude\ *|*@anthropic-ai/claude-code*) kill -9 "${_p#/proc/}" 2>/dev/null || true ;;
  esac
done
sleep 1
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

# --- EDIT: run the two groups. Each command must write JUnit XML. Do not let a
# --- failure in one group stop the other (no `set -e`).
cd /tmp
PYT="python3 -m pytest -q -p no:cacheprovider -o asyncio_mode=auto"

# Hidden behavioural tests, each driving a real public load of a prompt.
$PYT /tests/security --junitxml=/logs/verifier/security/results.xml

# Legitimate-use tests (the coupled behaviour of every lever).
$PYT /tests/functional --ignore=/tests/functional/project \
    --junitxml=/logs/verifier/functional/results.xml

# The project's own tests for the affected area, from pristine copies shipped
# under /tests (the agent may have edited /app). Each file runs in its own
# pytest process: the loader suite installs an asyncio event loop that the
# tool-dispatch suite's own loop management does not expect, so sharing a
# process makes a handful of unrelated async cases flake.
$PYT /tests/functional/project/test_loader.py \
    --junitxml=/logs/verifier/functional/project_loader.xml
$PYT /tests/functional/project/test_tool_dispatch.py \
    --junitxml=/logs/verifier/functional/project_tooldispatch.xml

python3 /tests/score.py
