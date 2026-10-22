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

KERNEL=/app/kernel
export PATH="/usr/local/go/bin:$PATH"
export CGO_ENABLED=1
export GOFLAGS=-mod=mod
export GOPROXY=off
export GOTOOLCHAIN=local

# Hidden behavioural tests, copied into the packages they drive. These are the
# only copies that are trusted.
cp /tests/harness/server_pub_fixture_test.go "$KERNEL/server/"
cp /tests/harness/api_pub_fixture_test.go "$KERNEL/api/"
cp /tests/security/server_static_access_test.go "$KERNEL/server/"
cp /tests/security/api_listing_access_test.go "$KERNEL/api/"
cp /tests/functional/server_static_use_test.go "$KERNEL/server/"
cp /tests/functional/api_listing_use_test.go "$KERNEL/api/"

# The project's own tests for the affected area, restored from pristine copies
# shipped under /tests (the agent may have edited /app).
cp /tests/functional/project/serve_assets_test.go "$KERNEL/server/"
cp /tests/functional/project/serve_svg_test.go "$KERNEL/server/"
cp /tests/functional/project/publish_access_test.go "$KERNEL/model/"
cp /tests/functional/project/block_test.go "$KERNEL/api/"
cp /tests/functional/project/filetree_test.go "$KERNEL/api/"

cd "$KERNEL" || exit 1

run_group() {
  local pkg="$1" pattern="$2" out="$3"
  go test "./$pkg/" -run "$pattern" -count=1 -timeout 300s -json 2>&1 \
    | python3 /tests/junit.py "$out" >/dev/null 2>&1
}

# Hidden behavioural tests.
run_group server '^TestPubAccess' /logs/verifier/security/server.xml
run_group api    '^TestPubAccess' /logs/verifier/security/api.xml
run_group server '^TestPubUse'    /logs/verifier/functional/server.xml
run_group api    '^TestPubUse'    /logs/verifier/functional/api.xml

# The project's own tests for the affected area.
run_group server '^(TestIsValidAssetRequestPath|TestAssetRequestPathURLDecoding|TestServeSVG.*)$' \
  /logs/verifier/functional/project_server.xml
run_group model  '^(TestCheckBlockTreeAccessableByPublishAccess|TestCheckBlockTreeMetadataAccessableByPublishAccess|TestCheckAttributeViewItemIDAccessableByPublishAccess|TestCheckAttributeViewBlockTreesAccessableByPublishAccess|TestFilterAttributeViewRelatedValuesByPublishAccess|TestFilterAttributeViewRelatedValuesKeepsPublicResponse|TestFilterSearchDocsByPublishAccess|TestFilterGraphByPublishAccess|TestFilterEmbedBlocksByPublishAccessRemovesInternalFields|TestFilterEmbedBlocksByPublishAccessDropsInaccessibleResults)$' \
  /logs/verifier/functional/project_model.xml
run_group api    '^(TestFilterBlockIDsByPublishAccess|TestFilterFileTreePublishAccess|TestSetSortRejectsInvalidRequest)$' \
  /logs/verifier/functional/project_api.xml

python3 /tests/score.py
