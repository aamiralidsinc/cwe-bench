#!/bin/bash
# Verifier entry point. Runs the hidden tests against whatever is in /app and
# writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Never trust test files inside /app: the agent could have edited them. Run
# only the copies under /tests.
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

# --- EDIT: run the two groups. Each command must write JUnit XML. Do not let a
# --- failure in one group stop the other (no `set -e`).
# Example for a Python project:
#   cd /app
#   python -m pytest /tests/security   -q -p no:cacheprovider --junitxml=/logs/verifier/security/results.xml
#   python -m pytest /tests/functional -q -p no:cacheprovider --junitxml=/logs/verifier/functional/results.xml

python3 /tests/score.py
