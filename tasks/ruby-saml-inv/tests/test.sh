#!/bin/bash
# Verifier entry point. Runs the two test groups against the ruby-saml source in
# /app and writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Tests and fixtures are taken only from /tests (never from /app).

# Stop the agent before grading (2026-10-16). On an agent timeout Harbor stops waiting for the
# agent but does not kill it inside this shared container, and it was seen editing /app while
# the tests ran (research/own-runs; build/postmortem.py). Kill every Claude Code process first.
for _p in /proc/[0-9]*; do
  case "$(tr '\0' ' ' < "$_p/cmdline" 2>/dev/null)" in
    claude\ *|*/claude\ *|*@anthropic-ai/claude-code*) kill -9 "${_p#/proc/}" 2>/dev/null || true ;;
  esac
done
sleep 1
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

ruby /tests/security/group.rb
ruby /tests/functional/group.rb

python3 /tests/score.py
