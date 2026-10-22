#!/bin/bash
# Verifier entry point. Runs the hidden tests against whatever is in /app, writing
# JUnit XML into /logs/verifier/{security,functional}/, then scores. Everything
# here runs offline (no network). Never trust test files inside /app: the agent
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

# --- EDIT: run the two groups. Each command must write JUnit XML. Do not let a
# --- failure in one group stop the other (no `set -e`).
SKIPS="-Dspotbugs.skip=true -Dcheckstyle.skip=true -Denforcer.skip=true \
-Dspotless.check.skip=true -Dspotless.apply.skip=true -Dmaven.javadoc.skip=true \
-Dlicense.skip=true -Dforbiddenapis.skip=true -Daccess-modifier-checker.skip=true"

cd /app

# Grade only the hidden tests: drop the project's own test sources (and any the
# agent may have touched) and drop in the copies from /tests.
rm -rf src/test/java src/test/resources
mkdir -p src/test/java/com/amazon/jenkins/ec2fleet
cp /tests/security/*.java /tests/functional/*.java src/test/java/com/amazon/jenkins/ec2fleet/

# Compile the (possibly fixed) product with the hidden tests and run them, offline.
mvn -B -o test $SKIPS -Dmaven.test.failure.ignore=true \
    > /logs/verifier/mvn.log 2>&1

# Split the surefire reports into the two groups by class name.
for f in target/surefire-reports/TEST-*.xml; do
  [ -f "$f" ] || continue
  case "$(basename "$f")" in
    *Security*)   cp "$f" /logs/verifier/security/   ;;
    *Functional*) cp "$f" /logs/verifier/functional/ ;;
  esac
done

python3 /tests/score.py
