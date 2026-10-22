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
PYT="python3 -m pytest -q -p no:cacheprovider"

# Hidden behavioural tests, each driving a real public file-search / file-tool call.
cd /tmp
$PYT /tests/security   --junitxml=/logs/verifier/security/results.xml
$PYT /tests/functional --ignore=/tests/functional/project \
    --junitxml=/logs/verifier/functional/results.xml

# The project's own tests for the affected area, from pristine copies shipped
# under /tests (the agent may have edited /app). Each file is restored over its
# location in /app and run from its package root so the project's conftest and
# rootdir resolve; they exercise the agent's product edits, not edited tests.
LV1=/app/libs/langchain_v1
cp /tests/functional/project/test_file_search.py \
   "$LV1/tests/unit_tests/agents/middleware/implementations/test_file_search.py"
( cd "$LV1" && $PYT \
    tests/unit_tests/agents/middleware/implementations/test_file_search.py \
    --junitxml=/logs/verifier/functional/project_file_search.xml )

ANT=/app/libs/partners/anthropic
cp /tests/functional/project/test_anthropic_tools.py \
   "$ANT/tests/unit_tests/middleware/test_anthropic_tools.py"
( cd "$ANT" && $PYT \
    tests/unit_tests/middleware/test_anthropic_tools.py \
    --junitxml=/logs/verifier/functional/project_anthropic_tools.xml )

python3 /tests/score.py
