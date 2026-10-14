#!/bin/bash
# Verifier entry point. Runs the two test groups against the ruby-saml source in
# /app and writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Tests and fixtures are taken only from /tests (never from /app).
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

ruby /tests/security/group.rb
ruby /tests/functional/group.rb

python3 /tests/score.py
