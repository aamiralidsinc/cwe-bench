#!/bin/bash
# Offline helper: compile the project's Java sources in /workspace into a class directory.
# Usage: /opt/fm/build.sh [output-dir]   (default: /tmp/fm-classes)
set -eu
SRC=/workspace
OUT="${1:-/tmp/fm-classes}"
mkdir -p "$OUT"
find "$SRC/freemarker-core/src/main/java" -name '*.java' ! -name SunInternalXalanXPathSupport.java \
    > /tmp/fm-mainsrc.txt
javac -nowarn --release 8 -encoding UTF-8 -cp "/opt/fm/deps/*" -d "$OUT" \
    @/tmp/fm-mainsrc.txt $(find /opt/fm/gen -name '*.java')
mkdir -p "$OUT/freemarker"
cp -r "$SRC/freemarker-core/src/main/resources/." "$OUT/"
cp "$SRC/freemarker-core/src/main/resource-templates/freemarker/version.properties" "$OUT/freemarker/"
echo "Compiled the project sources into $OUT"
