#!/bin/bash
# Compile the container's core sources with the JDK 8 compiler at the project's
# language level (1.6). The XML parser bundled with this tree does not read class
# files newer than that.
#   tomcat-build [SOURCE_DIR] [OUTPUT_DIR]
set -e
SRC=${1:-/workspace}
OUT=${2:-$SRC/output/classes}
rm -rf "$OUT"
mkdir -p "$OUT"
cd "$SRC"
find java -name '*.java' \
  ! -path '*/org/apache/catalina/ant/*' \
  ! -path '*/org/apache/tomcat/buildutil/*' \
  ! -path '*/org/apache/catalina/tribes/*' \
  ! -path '*/org/apache/catalina/ha/*' \
  ! -path '*/org/apache/jasper/compiler/AntCompiler.java' \
  ! -path '*/org/apache/naming/factory/webservices/*' \
  ! -name 'JDTCompiler.java' ! -name 'JspC.java' > "$OUT/.sources"
javac -nowarn -encoding ISO-8859-1 -source 1.6 -target 1.6 -d "$OUT" @"$OUT/.sources"
rm -f "$OUT/.sources"
cd java
find . -type f ! -name '*.java' | while read -r f; do
  mkdir -p "$OUT/$(dirname "$f")"
  cp "$f" "$OUT/$f"
done
