#!/bin/bash
# Verifier entry point. Rebuilds whatever is in /app and runs the hidden tests,
# writing JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Everything here runs offline. Never trust test files inside /app: the agent
# could have edited them. Run only the copies under /tests.

# Stop the agent before grading. On an agent timeout Harbor stops waiting for the agent but
# does not kill it inside this shared container; in round 1 it kept editing /app while the
# tests ran. Kill every Claude Code process first. Do not remove this block.
for _p in /proc/[0-9]*; do
  case "$(tr '\0' ' ' < "$_p/cmdline" 2>/dev/null)" in
    claude\ *|*/claude\ *|*@anthropic-ai/claude-code*) kill -9 "${_p#/proc/}" 2>/dev/null || true ;;
  esac
done
sleep 1
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

# --- EDIT: build the (possibly fixed) product and run the hidden tests, offline.
S="-Dmaven.build.cache.enabled=false -Dspotbugs.skip=true -Dcheckstyle.skip=true \
-Denforcer.skip=true -Dspotless.check.skip=true -Dspotless.apply.skip=true \
-Dmaven.javadoc.skip=true -Dlicense.skip=true -Dforbiddenapis.skip=true \
-Daccess-modifier-checker.skip=true -Dmaven.buildNumber.skip=true \
-Dmaven.test.failure.ignore=true"

cd /app

# Grade only the hidden tests: drop the module's test sources (and anything the
# agent may have touched there) and drop in the copies from /tests.
rm -rf jetty-core/jetty-security/src/test
D=jetty-core/jetty-security/src/test/java/org/eclipse/jetty/security
mkdir -p "$D"
cp /tests/support/*.java /tests/security/*.java /tests/functional/*.java "$D/"

# Compile and install the (possibly fixed) product modules, then run the tests.
mvn -o -B -pl jetty-core/jetty-util,jetty-core/jetty-security install -DskipTests $S \
    > /logs/verifier/mvn-build.log 2>&1
mvn -o -B -pl jetty-core/jetty-security test -Dtest='Security*,Functional*' -DfailIfNoTests=false $S \
    > /logs/verifier/mvn-test.log 2>&1

# Split the surefire reports into the two groups by class name.
for f in jetty-core/jetty-security/target/surefire-reports/TEST-*.xml; do
  [ -f "$f" ] || continue
  case "$(basename "$f")" in
    *Security*)   cp "$f" /logs/verifier/security/   ;;
    *Functional*) cp "$f" /logs/verifier/functional/ ;;
  esac
done

python3 /tests/score.py
