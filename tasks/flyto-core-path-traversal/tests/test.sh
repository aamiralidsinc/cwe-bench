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
cd /app
rm -rf /tmp/flyto-grading
export FLYTO_GRADING_ROOT=/tmp/flyto-grading
PYT="python3 -m pytest -q -c /tests/pytest.ini --rootdir /tests"
# Hidden behavioural tests, driven through POST /v1/execute.
$PYT /tests/security --junitxml=/logs/verifier/security/results.xml
$PYT /tests/functional --ignore=/tests/functional/project \
    --junitxml=/logs/verifier/functional/results.xml
# The project's own tests for the affected modules, from pristine copies (the agent may have
# edited /app/tests). These tests write through pytest's tmp_path (--basetemp) and through the
# tempfile module (TMPDIR); both point inside the sandbox, so a guard placed at the low-level
# writer is not punished for the tests' own scratch files.
cp -r /tests/functional/project/tests/. /app/tests/
mkdir -p /tmp/flyto-grading/sandbox/tmp
TMPDIR=/tmp/flyto-grading/sandbox/tmp FLYTO_SANDBOX_DIR=/tmp/flyto-grading/sandbox python3 -m pytest -q -p no:cacheprovider -o addopts= \
    --basetemp=/tmp/flyto-grading/sandbox/project-tmp \
    tests/modules/test_new_modules.py::TestImageModules tests/browser/test_checkpoint.py \
    --junitxml=/logs/verifier/functional/project.xml

python3 /tests/score.py
