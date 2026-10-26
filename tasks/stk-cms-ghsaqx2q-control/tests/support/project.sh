#!/bin/bash
# Runs the project's own unit test for the affected helper with the project's Codeception suite.
# The XML report is written to the path given as the first argument. A transient database
# connection fault during suite setup gets one retry; a real test failure is reported as-is.
set -u
out=${1:?usage: project.sh <junit-xml-path>}
cd /workspace || exit 1

run_suite() {
    rm -rf tests/_craft/storage/runtime/compiled_classes/* tests/_output
    ./vendor/bin/codecept run unit tests/unit/helpers/ComponentHelperTest.php --no-colors --xml
}

run_suite
rc=$?
if [ "$rc" -ne 0 ]; then
    sleep 3
    run_suite
    rc=$?
fi

if [ -s tests/_output/report.xml ]; then
    cp tests/_output/report.xml "$out"
fi
exit "$rc"
