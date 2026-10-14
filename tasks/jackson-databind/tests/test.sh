#!/bin/bash
# Verifier entry point. Runs the hidden tests against whatever is in /app and
# writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Never trust test files inside /app: the agent could have edited them. Run
# only the copies under /tests.
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

# --- EDIT: run the two groups. Each command must write JUnit XML. Do not let a
# --- failure in one group stop the other (no `set -e`).
CORE=/opt/libs/jackson-core-2.18.4.jar:/opt/libs/jackson-annotations-2.18.4.jar
JUNIT=/opt/libs/junit-platform-console-standalone-1.11.4.jar
WORK=/tmp/verify
rm -rf "$WORK"
mkdir -p "$WORK/classes" "$WORK/tests" "$WORK/gen/com/fasterxml/jackson/databind/cfg"

# 1) Generate the build-time version class from the in-repo template.
sed -e 's/@package@/com.fasterxml.jackson.databind.cfg/' \
    -e 's/@projectversion@/2.18.9-SNAPSHOT/' \
    -e 's/@projectgroupid@/com.fasterxml.jackson.core/' \
    -e 's/@projectartifactid@/jackson-databind/' \
    /app/src/main/java/com/fasterxml/jackson/databind/cfg/PackageVersion.java.in \
    > "$WORK/gen/com/fasterxml/jackson/databind/cfg/PackageVersion.java"

# 2) Compile the library as modified by the agent (offline).
( cd /app && find src/main/java -name '*.java' > "$WORK/srcs.txt" )
echo "$WORK/gen/com/fasterxml/jackson/databind/cfg/PackageVersion.java" >> "$WORK/srcs.txt"
javac -nowarn -proc:none -cp "$CORE" -d "$WORK/classes" @"$WORK/srcs.txt"

# 3) Compile the hidden tests against the freshly built library.
find /tests/support /tests/security /tests/functional -name '*.java' > "$WORK/tsrcs.txt"
javac -proc:none -cp "$CORE:$WORK/classes:$JUNIT" -d "$WORK/tests" @"$WORK/tsrcs.txt"

# 4) Run each group through the real public API, emitting JUnit XML.
java -jar "$JUNIT" execute -cp "$CORE:$WORK/classes:$WORK/tests" \
     --select-package security   --reports-dir=/logs/verifier/security   --disable-banner >/dev/null 2>&1
java -jar "$JUNIT" execute -cp "$CORE:$WORK/classes:$WORK/tests" \
     --select-package functional --reports-dir=/logs/verifier/functional --disable-banner >/dev/null 2>&1

python3 /tests/score.py
