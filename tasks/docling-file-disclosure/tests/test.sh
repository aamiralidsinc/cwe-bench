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
# Pristine copies of the project's own tests for the area and of its in-process
# service fake (the security tests drive the service client against it). The
# agent may have edited /app/tests; never trust those copies.
cp -r /tests/functional/project/tests/. /app/tests/
# Hidden behavioural tests (public SDK entry points, files in temp dirs).
python3 -m pytest /tests/security -q -p no:cacheprovider -W ignore \
    --junitxml=/logs/verifier/security/results.xml
python3 -m pytest /tests/functional -q -p no:cacheprovider -W ignore --ignore=/tests/functional/project \
    --junitxml=/logs/verifier/functional/results.xml
# The project's own tests for Docling JSON input, the service client and the
# DCLX archive backend (all offline; no ML models needed).
python3 -m pytest -q -p no:cacheprovider -W ignore \
    tests/test_backend_docling_json.py \
    tests/test_service_client_fake_service.py \
    tests/test_service_client_sdk_unit.py \
    tests/test_service_client_payload_fidelity.py \
    tests/test_service_datamodels.py \
    tests/test_backend_dclx.py \
    --junitxml=/logs/verifier/functional/project.xml

python3 /tests/score.py
