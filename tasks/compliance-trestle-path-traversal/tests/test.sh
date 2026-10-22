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
# Hidden behavioural tests (drive the real `trestle` CLI in temporary workspaces).
python3 -m pytest /tests/security -q -p no:cacheprovider -n 2 \
    --junitxml=/logs/verifier/security/results.xml
python3 -m pytest /tests/functional -q -p no:cacheprovider -n 2 --ignore=/tests/functional/project \
    --junitxml=/logs/verifier/functional/results.xml
# The project's own tests for the affected commands, from pristine copies (the agent may
# have edited /app/tests). Tests that need the internet are deselected (offline grading).
cp -r /tests/functional/project/tests/. /app/tests/
python3 -m pytest -q -p no:cacheprovider -n 2 \
    tests/trestle/utils/fs_test.py \
    tests/trestle/core/commands/author/catalog_test.py \
    tests/trestle/core/commands/author/prof_test.py \
    tests/trestle/core/commands/author/ssp_test.py \
    tests/trestle/core/commands/author/component_test.py \
    tests/trestle/core/commands/author/headers_test.py \
    tests/trestle/core/commands/author/docs_test.py \
    tests/trestle/core/commands/author/folders_test.py \
    tests/trestle/core/commands/create_test.py \
    tests/trestle/core/commands/replicate_test.py \
    tests/trestle/core/commands/import__test.py \
    --deselect tests/trestle/core/commands/author/ssp_test.py::test_ssp_generate_aggregates_no_cds \
    --deselect tests/trestle/core/commands/author/ssp_test.py::test_ssp_generate_aggregates_no_param_value_orig \
    --deselect tests/trestle/core/commands/author/ssp_test.py::test_ssp_generate_missing_profile_param_value_origin_regression \
    --deselect tests/trestle/core/commands/author/ssp_test.py::test_ssp_assemble_fedramp_profile \
    --deselect tests/trestle/core/commands/author/prof_test.py::test_profile_generate_assemble_rev_5 \
    --deselect tests/trestle/core/commands/import__test.py::test_import_from_url \
    --deselect tests/trestle/core/commands/import__test.py::test_import_from_nist \
    --junitxml=/logs/verifier/functional/project.xml

python3 /tests/score.py
