#!/bin/bash
# Native runner for one hidden group. Invoked as `agent` by /tests/test.sh with the
# group name and an agent-writable directory for the JUnit XML. Every suite runs
# through the project's own Jest setup (Backstage CLI) inside the restored workspace;
# a failing suite never stops the next one.
set -u
group="${1:?usage: run-group.sh <security|functional> <outdir>}"
out="${2:?usage: run-group.sh <security|functional> <outdir>}"
mkdir -p "$out"

export CI=1
ROOT="${ROOT:-/workspace}"
CLI=$ROOT/node_modules/.bin/backstage-cli
JUNIT_REPORTER=/opt/junit/node_modules/jest-junit

GH=$ROOT/plugins/scaffolder-backend-module-github
GL=$ROOT/plugins/scaffolder-backend-module-gitlab
CJ=$ROOT/plugins/scaffolder-backend-module-cookiecutter
SB=$ROOT/plugins/scaffolder-backend
FETCH=$SB/src/scaffolder/actions/builtin/fetch

run() {  # <package dir> <report name> <test paths...>
  local pkg="$1" name="$2"
  shift 2
  (
    cd "$pkg" || exit 1
    JEST_JUNIT_OUTPUT_DIR="$out" JEST_JUNIT_OUTPUT_NAME="$name.xml" \
      "$CLI" package test --ci --watchAll=false \
      --reporters=default --reporters="$JUNIT_REPORTER" \
      --runTestsByPath "$@"
  ) >"$out/$name.log" 2>&1 || true
}

case "$group" in
  security)
    run "$GH" github src/__verifier__/github_security.test.ts
    run "$GL" gitlab src/__verifier__/gitlab_security.test.ts
    run "$SB" fetch \
      src/scaffolder/actions/builtin/fetch/__verifier__/fetch_security.test.ts
    run "$CJ" cookiecutter src/__verifier__/cookiecutter_security.test.ts
    ;;
  functional)
    run "$GH" github \
      src/__verifier__/github_functional.test.ts src/util.test.ts
    run "$GL" gitlab \
      src/__verifier__/gitlab_functional.test.ts src/util.test.ts
    run "$SB" fetch \
      src/scaffolder/actions/builtin/fetch/__verifier__/fetch_functional.test.ts \
      src/scaffolder/actions/builtin/fetch/plain.test.ts \
      src/scaffolder/actions/builtin/fetch/template.test.ts
    run "$CJ" cookiecutter src/__verifier__/cookiecutter_functional.test.ts
    ;;
  *)
    echo "unknown group: $group" >&2
    exit 2
    ;;
esac

exit 0
