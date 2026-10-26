#!/bin/bash
# Compile one hidden group against the built product and run it, always leaving a JUnit XML
# behind (a compile or start-up failure is a failing group, never a missing result).
set -u
G=$1
OUT=$2
S=/workspace/.htests
CP="/workspace/core/target/classes:/workspace/test/target/classes:$(cat /opt/jk-cp.txt)"
JAVA_HOME=/opt/java/openjdk
export JAVA_HOME
JAVAC="$JAVA_HOME/bin/javac"
JAVA="$JAVA_HOME/bin/java"

failxml() {
  {
    printf '<?xml version="1.0" encoding="UTF-8"?>\n'
    printf '<testsuite name="security-fix" tests="1" failures="1" errors="0" skipped="0">\n'
    printf ' <testcase classname="hudson.security.bt.%s" name="group">\n' "$G"
    printf '  <failure message="%s">%s</failure>\n' "$1" "$1"
    printf ' </testcase>\n</testsuite>\n'
  } > "$OUT"
}

D="$S/classes-$G"
rm -rf "$D"
mkdir -p "$D"
if ! "$JAVAC" -nowarn -cp "$CP" -d "$D" $S/harness/*.java $S/$G/*.java > "$S/javac-$G.log" 2>&1; then
  failxml "the group could not be compiled against the submitted code"
  tail -40 "$S/javac-$G.log"
  exit 0
fi

CLASSES=""
for f in $S/$G/*.java; do
  CLASSES="$CLASSES hudson.security.bt.$(basename "$f" .java)"
done

cd /workspace || exit 0
"$JAVA" -cp "$D:$CP" hudson.security.bt.JUnitXmlRunner "$OUT" $CLASSES > "$S/run-$G.log" 2>&1
rc=$?
cat "$S/run-$G.log"
[ -s "$OUT" ] || failxml "the group produced no results (exit $rc)"
exit 0
