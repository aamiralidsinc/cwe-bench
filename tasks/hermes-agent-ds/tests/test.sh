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

# Hidden tests live outside the product tree: make the product root and the
# shared helper module importable from any pytest rootdir.
export PYTHONPATH="/app:/tests${PYTHONPATH:+:$PYTHONPATH}"

# Hidden behavioural tests: the real product entry points, in-process.
cd /app
$PYT /tests/security --junitxml=/logs/verifier/security/results.xml
$PYT /tests/functional --ignore=/tests/functional/project --junitxml=/logs/verifier/functional/results.xml

# The project's own tests for the affected area, from pristine copies shipped
# under /tests (the agent may have edited /app). Each file is restored over its
# location in /app and run from /app so the project's conftest resolves; they
# exercise the agent's product edits, not edited tests.
mkdir -p /app/tests/tools /app/tests/agent/transports
cp /tests/functional/project/test_memory_tool.py /app/tests/tools/test_memory_tool.py
cp /tests/functional/project/test_memory_tool_schema.py /app/tests/tools/test_memory_tool_schema.py
cp /tests/functional/project/test_prompt_builder.py /app/tests/agent/test_prompt_builder.py
cp /tests/functional/project/test_subdirectory_hints.py /app/tests/agent/test_subdirectory_hints.py
cp /tests/functional/project/test_codex_event_projector.py /app/tests/agent/transports/test_codex_event_projector.py

cd /app
$PYT tests/tools/test_memory_tool.py tests/tools/test_memory_tool_schema.py \
    --junitxml=/logs/verifier/functional/project_memory.xml
$PYT tests/agent/test_prompt_builder.py tests/agent/test_subdirectory_hints.py \
    --junitxml=/logs/verifier/functional/project_context.xml
$PYT tests/agent/transports/test_codex_event_projector.py \
    --junitxml=/logs/verifier/functional/project_transport.xml

python3 /tests/score.py
