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
-Dlicense.skip=true -Dforbiddenapis.skip=true"
P="-P !mustache-specs"

cd /app
# git-build-hook (bound by the parent POM) needs a repository to exist.
[ -d .git ] || git init -q .
git config user.email ci@example.com 2>/dev/null || true
git config user.name ci 2>/dev/null || true
mkdir -p handlebars/src/test/resources/mustache

# Grade only the hidden tests: drop the module's own test sources (and any the
# agent may have touched) and drop in the copies from /tests.
rm -rf handlebars-springmvc/src/test/java handlebars-springmvc/target/test-classes
mkdir -p handlebars-springmvc/src/test/java/com/github/jknack/handlebars/springmvc
cp /tests/security/*.java /tests/functional/*.java \
   handlebars-springmvc/src/test/java/com/github/jknack/handlebars/springmvc/

# Rebuild the (possibly fixed) core module from source and install it, then run the
# hidden tests against the Spring MVC module. All offline.
mvn -B -o -q $P -N install $SKIPS >/logs/verifier/mvn-parent.log 2>&1
mvn -B -o -q $P -pl handlebars install -DskipTests $SKIPS >/logs/verifier/mvn-core.log 2>&1
mvn -B -o $P -pl handlebars-springmvc test $SKIPS -Dmaven.test.failure.ignore=true \
    >/logs/verifier/mvn-test.log 2>&1

# Split the surefire reports into the two groups by class name.
for f in handlebars-springmvc/target/surefire-reports/TEST-*.xml; do
  [ -f "$f" ] || continue
  case "$(basename "$f")" in
    *Security*)   cp "$f" /logs/verifier/security/   ;;
    *Functional*) cp "$f" /logs/verifier/functional/ ;;
  esac
done

python3 /tests/score.py
