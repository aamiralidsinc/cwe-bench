#!/bin/bash
# Verifier entry point. Runs the hidden tests against whatever is in /app and
# writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Never trust test files inside /app: the agent could have edited them. Run
# only the copies under /tests.

# Stop the agent before grading. On an agent timeout Harbor stops waiting for the agent but
# does not kill it inside this shared container; it could otherwise keep editing /app while
# the tests run. Kill every Claude Code process first. Do not remove this block.
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

# Hidden behavioural tests. Driven from /tests so the shared conftest at the
# rootdir is loaded for both groups. They import the installed mcp_atlassian
# package, which reflects the agent's edits in /app (editable install).
cd /tests
$PYT security   --junitxml=/logs/verifier/security/results.xml
$PYT functional --ignore=/tests/functional/project \
    --junitxml=/logs/verifier/functional/results.xml

# The project's own tests for the affected area, restored from pristine copies
# shipped under /tests (the agent may have edited /app). They are run from the
# repo root so the project's rootdir, conftests and `src`/`tests` imports
# resolve. The tests that encode the *old* (pre-fix) upload/content-file
# behaviour are deselected: a correct fix changes that behaviour, so they are
# not valid acceptance tests here; the remainder guards unrelated area
# behaviour.
P=/tests/functional/project
cp "$P/jira_test_attachments.py"       /app/tests/unit/jira/test_attachments.py
cp "$P/confluence_test_attachments.py" /app/tests/unit/confluence/test_attachments.py
cp "$P/test_confluence_server.py"      /app/tests/unit/servers/test_confluence_server.py
cp "$P/test_jira_server.py"            /app/tests/unit/servers/test_jira_server.py
DESELECT=""
while IFS= read -r line; do
  [ -n "$line" ] && DESELECT="$DESELECT --deselect $line"
done < "$P/deselect.txt"
( cd /app && $PYT \
    tests/unit/jira/test_attachments.py \
    tests/unit/confluence/test_attachments.py \
    tests/unit/servers/test_confluence_server.py \
    tests/unit/servers/test_jira_server.py \
    $DESELECT \
    --junitxml=/logs/verifier/functional/project_area.xml )

python3 /tests/score.py
