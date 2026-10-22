#!/usr/bin/env bash
# Runs the hidden functional suite as the unprivileged verifier user. $1 is the
# agent-writable directory where the JUnit XML must be written.
set -uo pipefail
OUT="${1:?output directory}"
cd /workspace || exit 1
S="-Dmaven.repo.local=/opt/m2 -Dspotbugs.skip=true -Dcheckstyle.skip=true -Denforcer.skip=true \
-Dspotless.check.skip=true -Dspotless.apply.skip=true -Dmaven.javadoc.skip=true \
-Dlicense.skip=true -Dforbiddenapis.skip=true -Daccess-modifier-checker.skip=true \
-Dassembly.skipAssembly=true -Dmaven.test.failure.ignore=true -DfailIfNoTests=false"

rm -rf hazelcast/target/test-classes hazelcast/target/surefire-reports
mkdir -p hazelcast/target/test-classes
CP="$(cat /opt/hazelcast-test-cp.txt):hazelcast/target/classes"
javac --release 17 -nowarn -cp "$CP" -d hazelcast/target/test-classes \
    .htests/support/*.java .htests/functional/*.java
rc=$?
if [ "$rc" -ne 0 ]; then
  printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?><testsuite name="benchkit.Compile" tests="1" failures="1"><testcase classname="benchkit.Compile" name="hiddenTestsCompile"><failure message="the submission does not compile against the hidden suite"/></testcase></testsuite>' > "$OUT/compile.xml"
  exit 0
fi

mvn -o -B -pl hazelcast surefire:test -Dtest='Functional*' $S
cp hazelcast/target/surefire-reports/TEST-*.xml "$OUT"/ 2>/dev/null || true
exit 0
