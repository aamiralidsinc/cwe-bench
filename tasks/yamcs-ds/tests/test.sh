#!/bin/bash
# Verifier entry point. Runs the hidden tests against whatever is in /app, writing
# JUnit XML into /logs/verifier/{security,functional}/, then scores. Everything
# here runs offline (no network). Never trust test files inside /app: the agent
# could have edited them. Run only the copies under /tests.

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

cd /app

# Restore the integration harness, the test configuration and the MDB data from
# the verifier's copies, then install the hidden tests. Nothing under /app that
# the agent could have edited is trusted for grading.
rm -rf tests/src/main/java/org/yamcs/tests \
       tests/src/test/java \
       tests/src/test/resources \
       tests/mdb
mkdir -p tests/src/main/java/org/yamcs/tests \
         tests/src/test/java/org/yamcs/tests \
         tests/src/test/resources \
         tests/mdb
cp /tests/harness/main/*.java tests/src/main/java/org/yamcs/tests/
cp -r /tests/harness/project/. tests/src/test/java/
cp -r /tests/harness/HiddenIT tests/src/test/resources/
cp /tests/harness/logging.properties tests/src/test/resources/
cp /tests/security/*.java /tests/functional/*.java tests/src/test/java/org/yamcs/tests/
cp -r /tests/mdb/. tests/mdb/

# Rebuild the product from the (possibly fixed) sources, then run the hidden
# suite offline. A build failure leaves the XML directories empty, which scores
# as a failure.
mvn -B -o -q -Dmaven.test.skip=true -Dmaven.javadoc.skip=true -Denforcer.skip=true \
    -pl yamcs-api,yamcs-xtce,yamcs-client,yamcs-core -am install \
    > /logs/verifier/build.log 2>&1
mvn -B -o -Dmaven.javadoc.skip=true -Denforcer.skip=true \
    -pl tests test -Dtest='Security*,Functional*' \
    -Dsurefire.failIfNoSpecifiedTests=false -DfailIfNoTests=false \
    > /logs/verifier/mvn.log 2>&1

# Split the surefire reports into the two groups by class name.
for f in tests/target/surefire-reports/TEST-*.xml; do
  [ -f "$f" ] || continue
  case "$(basename "$f")" in
    *Security*)   cp "$f" /logs/verifier/security/ ;;
    *Functional*) cp "$f" /logs/verifier/functional/ ;;
  esac
done

python3 /tests/score.py
