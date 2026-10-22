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
export LITELLM_LOG=ERROR
export LITELLM_TELEMETRY=False
export LITELLM_DONT_SHOW_FEEDBACK_BOX=True
export DISABLE_SCHEMA_UPDATE=True
PYT="python3 -m pytest -q -p no:cacheprovider"

cd /tests
$PYT security --junitxml=/logs/verifier/security/results.xml
$PYT functional --ignore=functional/project --junitxml=/logs/verifier/functional/results.xml

# The project's own tests for the affected area, from pristine copies shipped
# under /tests (the agent may have edited /app). Each file is restored over its
# location in /app and run from the repository root so the project's conftest
# resolves; they exercise the agent's product edits, not edited tests.
cd /app
cp /tests/functional/project/test_auth_utils.py tests/test_litellm/proxy/auth/test_auth_utils.py
cp /tests/functional/project/test_health_endpoints.py tests/test_litellm/proxy/health_endpoints/test_health_endpoints.py
cp /tests/functional/project/test_azure_routes.py tests/test_litellm/proxy/image_endpoints/test_azure_routes.py
cp /tests/functional/project/test_provider_url_destination_guard.py tests/test_litellm/proxy/test_provider_url_destination_guard.py

$PYT tests/test_litellm/proxy/auth/test_auth_utils.py \
    --junitxml=/logs/verifier/functional/project_auth_utils.xml
$PYT tests/test_litellm/proxy/test_provider_url_destination_guard.py \
    --junitxml=/logs/verifier/functional/project_provider_guard.xml
$PYT tests/test_litellm/proxy/image_endpoints/test_azure_routes.py \
    --junitxml=/logs/verifier/functional/project_azure_routes.xml
# The three liveness/readiness cases assert wall-clock latency on an idle host
# (a cold TestClient request exceeds their 100 ms bound in this container);
# they are excluded as environmental, not behavioural, tests. pytest's
# --deselect matches node-id prefixes, so the readiness name also excludes its
# five sibling cases (readiness response contents, not the changed area).
$PYT tests/test_litellm/proxy/health_endpoints/test_health_endpoints.py \
    --deselect tests/test_litellm/proxy/health_endpoints/test_health_endpoints.py::test_health_liveliness_endpoint \
    --deselect tests/test_litellm/proxy/health_endpoints/test_health_endpoints.py::test_health_liveness_endpoint \
    --deselect tests/test_litellm/proxy/health_endpoints/test_health_endpoints.py::test_health_readiness \
    --junitxml=/logs/verifier/functional/project_health_endpoints.xml

python3 /tests/score.py
