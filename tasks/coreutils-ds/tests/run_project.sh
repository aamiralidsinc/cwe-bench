#!/usr/bin/env bash
# Run the project's own install tests with nextest and write their JUnit report to the path
# given as the first argument. Runs as the unprivileged `agent` user from /workspace.
set -u
OUT="$1"
cd /workspace || exit 1
export CARGO_HOME=/usr/local/cargo
export RUSTUP_HOME=/usr/local/rustup
export CARGO_NET_OFFLINE=1
export CARGO_TERM_COLOR=never
JUNIT=/workspace/target/nextest/ci/junit.xml
rm -f "$JUNIT"
cargo nextest run --offline --no-default-features --features install \
    -p coreutils --test tests --profile ci -E 'test(/^test_install::/)'
if [ -s "$JUNIT" ]; then
  cp -f "$JUNIT" "$OUT"
else
  # No report means the project tests could not be built or run: count that as a failure in the
  # functional group rather than silently dropping it.
  printf '%s\n' \
    '<?xml version="1.0" encoding="UTF-8"?>' \
    '<testsuite name="project-install" tests="1" failures="1">' \
    '<testcase classname="project" name="install-tests-ran"><failure message="the project install tests did not run"/></testcase>' \
    '</testsuite>' > "$OUT"
fi
