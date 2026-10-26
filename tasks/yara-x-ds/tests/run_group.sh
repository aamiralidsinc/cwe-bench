#!/usr/bin/env bash
# Run one hidden libtest group and convert its output to JUnit XML.
# Usage: run_group.sh <test-filter> <suite-name> <junit-out>
set -u
filter="$1"
suite="$2"
out="$3"
log="${out%.xml}.log"
cd /workspace || exit 1
CARGO_TARGET_DIR=/opt/target cargo test --offline -p yara-x --lib -- "$filter" --test-threads=1 > "$log" 2>&1
python3 /workspace/.htests/junit.py "$log" "$out" "$suite"
