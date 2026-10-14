#!/bin/bash
# Verifier entry point. Builds the client from whatever is in /app, then compiles
# and runs the hidden tests against it, writing JUnit XML into
# /logs/verifier/{security,functional}/, and finally scores.
# Never trust test files inside /app: the agent could have edited them. Run only
# the copies under /tests. Everything here runs offline (no network).
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

# --- EDIT: run the two groups. Each command must write JUnit XML. Do not let a
# --- failure in one group stop the other (no `set -e`).

# 1. Build the client library from the (possibly fixed) source, offline.
cd /app
mvn -q -o -pl client -am package \
    -Dmaven.test.skip=true -Dgpg.skip=true -Dspotbugs.skip=true \
    -Dcheckstyle.skip=true -Dlicense.skip=true -Denforcer.skip=true \
    -Dmaven.javadoc.skip=true -Dsource.skip=true > /logs/verifier/build.log 2>&1

APP_JAR=$(ls /app/client/target/async-http-client-*.jar 2>/dev/null | grep -v sources | head -1)
CP="${APP_JAR}:$(ls /opt/ahc-deps/*.jar | paste -sd:)"

# 2. Compile the verifier's own tests against that build.
rm -rf /tmp/tc && mkdir -p /tmp/tc
javac -cp "${CP}:/opt/junit-console.jar" -d /tmp/tc \
    /tests/common/StubServer.java /tests/security/SecurityTests.java /tests/functional/FunctionalTests.java \
    > /logs/verifier/javac.log 2>&1

# 3. Run each group through the real client API, emitting JUnit XML per group.
java -jar /opt/junit-console.jar execute -cp "${CP}:/tmp/tc" \
    --select-class=SecurityTests --reports-dir=/logs/verifier/security --disable-banner \
    > /logs/verifier/security.log 2>&1
java -jar /opt/junit-console.jar execute -cp "${CP}:/tmp/tc" \
    --select-class=FunctionalTests --reports-dir=/logs/verifier/functional --disable-banner \
    > /logs/verifier/functional.log 2>&1

python3 /tests/score.py
