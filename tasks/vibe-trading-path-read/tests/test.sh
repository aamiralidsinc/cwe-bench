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
cd /app/agent
rm -rf /tmp/vt-grading
mkdir -p /tmp/vt-grading
export VT_AGENT_DIR=/app/agent
PYT="python3 -m pytest -q -c /tests/pytest.ini --rootdir /tests"
# Hidden behavioural tests, each driving one tool call through the agent loop.
$PYT /tests/security --basetemp=/tmp/vt-grading/sec --junitxml=/logs/verifier/security/results.xml
$PYT /tests/functional --ignore=/tests/functional/project --basetemp=/tmp/vt-grading/fun \
    --junitxml=/logs/verifier/functional/results.xml
# The project's own tests for the affected tools, from pristine copies (the agent may have
# edited /app/agent/tests). Their temporary files live in a directory the operator setting
# allows, as a deployment that keeps documents there would configure it. test_missing_file
# probes a path outside every allowed directory, so it is not run. The shipped copies leave
# out tests that pin internal helpers (the loop's run_dir mapper, the path helpers' API).
cp -r /tests/functional/project/tests/. /app/agent/tests/
VIBE_TRADING_ALLOWED_FILE_ROOTS=/tmp/vt-grading/project python3 -m pytest -q -p no:cacheprovider -o addopts= \
    --basetemp=/tmp/vt-grading/project \
    tests/test_doc_reader.py tests/test_shadow_account.py \
    tests/test_upload_api.py tests/test_loop_helpers.py -k "not test_missing_file" \
    --junitxml=/logs/verifier/functional/project.xml

python3 /tests/score.py
