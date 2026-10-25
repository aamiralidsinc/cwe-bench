#!/usr/bin/env bash
# Runs one hidden group inside /workspace as the unprivileged runner.
#   run_group.sh <security|functional> <junit-xml-out>
# The hidden sources are copied from /opt/suites (readable after /tests is locked) into the
# project's own test source trees, the project's native runner (Maven Surefire) runs them, and
# every module's JUnit XML is merged into the requested output file.
set -u
group="$1"
out="$2"
cd /workspace || exit 1

base="${TMPDIR:-/tmp}/htests-run-$group"
rm -rf "$base"
mkdir -p "$base"

run_module() { # <module> <test-pattern> <report-dir>
    local module="$1" pattern="$2" dir="$3"
    mkdir -p "$dir"
    rm -rf "$module/target/surefire-reports"
    JAVA_HOME=/opt/java/openjdk ./mvnw -o -B -pl "$module" test \
        -Dtest="$pattern" -DfailIfNoTests=false -Dsurefire.failIfNoSpecifiedTests=false \
        -Dmaven.repo.local=/home/agent/.m2/repository \
        -Dformat.skip=true -Dmaven-enforcer-plugin.phase=none -Dforbiddenapis-maven-plugin.phase=none \
        -Ddevelocity.cache.local.enabled=false -Ddevelocity.cache.remote.enabled=false \
        > "$dir/mvn.log" 2>&1 || true
    cp "$module"/target/surefire-reports/*.xml "$dir"/ 2>/dev/null || true
}

case "$group" in
  security)
    cp /opt/suites/security/vertx-http/*.java \
        extensions/vertx-http/deployment/src/test/java/io/quarkus/vertx/http/security/ 2>/dev/null || true
    cp /opt/suites/security/undertow/*.java \
        extensions/undertow/deployment/src/test/java/io/quarkus/undertow/test/ 2>/dev/null || true
    run_module extensions/vertx-http/deployment \
        'HiddenStaticPathAuthzTest,HiddenStaticExcludedPathTest' "$base/vertx-http"
    run_module extensions/undertow/deployment \
        'HiddenServletPathAuthzTest' "$base/undertow"
    python3 /opt/suites/support/merge_junit.py "$out" "$base/vertx-http" "$base/undertow" security
    ;;
  functional)
    cp /opt/suites/functional/vertx-http/*.java \
        extensions/vertx-http/deployment/src/test/java/io/quarkus/vertx/http/security/ 2>/dev/null || true
    cp /opt/suites/functional/undertow/*.java \
        extensions/undertow/deployment/src/test/java/io/quarkus/undertow/test/ 2>/dev/null || true
    run_module extensions/vertx-http/deployment \
        'HiddenStaticPathAuthzFunctionalTest,ConfigBasedPathMatchingHttpSecurityPolicyTest' "$base/vertx-http"
    run_module extensions/undertow/deployment \
        'HiddenServletPathAuthzFunctionalTest,ServletWebXmlSecurityTestCase' "$base/undertow"
    python3 /opt/suites/support/merge_junit.py "$out" "$base/vertx-http" "$base/undertow" functional
    ;;
  *)
    echo "unknown group: $group" >&2
    exit 2
    ;;
esac
