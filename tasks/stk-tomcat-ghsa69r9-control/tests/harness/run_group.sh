#!/bin/bash
# Compile one hidden group against the built product and run it, always leaving a JUnit XML
# behind (a compile or start-up failure is a failing group, never a missing result).
set -u
G=$1
OUT=$2
S=/workspace/.htests
export JAVA_HOME=/opt/java/openjdk
export PATH="$JAVA_HOME/bin:$PATH"
CP="/workspace/output/classes:/opt/junit.jar:/opt/hamcrest.jar"
JAVAC=javac
JAVA=java

failxml() {
  {
    printf '<?xml version="1.0" encoding="UTF-8"?>\n'
    printf '<testsuite name="security-fix" tests="1" failures="1" errors="0" skipped="0">\n'
    printf ' <testcase classname="org.apache.catalina.tribes.htests.%s" name="group">\n' "$G"
    printf '  <failure message="%s">%s</failure>\n' "$1" "$1"
    printf ' </testcase>\n</testsuite>\n'
  } > "$OUT"
}

D="$S/classes-$G"
rm -rf "$D"
mkdir -p "$D"

SRCS="$S/harness/JUnitXmlRunner.java"
CLASSES=""
if [ "$G" = "security" ]; then
  for f in "$S"/security/*.java; do
    [ -e "$f" ] || continue
    SRCS="$SRCS $f"
    CLASSES="$CLASSES org.apache.catalina.tribes.group.interceptors.$(basename "$f" .java)"
  done
else
  for f in "$S"/functional/*.java; do
    [ -e "$f" ] || continue
    SRCS="$SRCS $f"
    CLASSES="$CLASSES org.apache.catalina.tribes.group.interceptors.$(basename "$f" .java)"
  done
  for f in "$S"/functional/project/*.java; do
    [ -e "$f" ] || continue
    SRCS="$SRCS $f"
  done
  CLASSES="$CLASSES org.apache.catalina.tribes.group.interceptors.TestEncryptInterceptor"
fi

if ! "$JAVAC" -nowarn -cp "$CP" -d "$D" $SRCS > "$S/javac-$G.log" 2>&1; then
  failxml "the group could not be compiled against the submitted code"
  tail -40 "$S/javac-$G.log"
  exit 0
fi

cd /workspace || exit 0
"$JAVA" -cp "$D:$CP" org.apache.catalina.tribes.htests.JUnitXmlRunner "$OUT" $CLASSES > "$S/run-$G.log" 2>&1
rc=$?
cat "$S/run-$G.log"
[ -s "$OUT" ] || failxml "the group produced no results (exit $rc)"
exit 0
