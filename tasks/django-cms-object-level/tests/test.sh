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
# The settings module and the shared fixtures live next to the tests; they are
# put on the import path from a private copy so nothing under /app shadows them.
H=$(mktemp -d)
cp /tests/cms_test_settings.py /tests/cmsfix.py "$H"/
export DJANGO_TESTS=1 PYTHONDONTWRITEBYTECODE=1
PYTEST=(python3 -m pytest -q -p no:cacheprovider --ds=cms_test_settings --rootdir="$H" -o pythonpath="$H"
        --import-mode=importlib -W ignore)
cd /app
"${PYTEST[@]}" /tests/security   --junitxml=/logs/verifier/security/results.xml
"${PYTEST[@]}" /tests/functional --junitxml=/logs/verifier/functional/results.xml

python3 /tests/score.py
