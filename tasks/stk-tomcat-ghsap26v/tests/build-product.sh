#!/bin/bash
# Verifier-side compiler for the restored checkout. The compiler settings match the
# agent image, but the file walk and output layout are this side's own.
set -eu
checkout=$1
destdir=$2
rm -rf "$destdir"
mkdir -p "$destdir"
cd "$checkout"
list=$(mktemp)
find java -name '*.java' -print | grep -v \
  -e '/catalina/ant/' -e '/tomcat/buildutil/' -e '/catalina/tribes/' -e '/catalina/ha/' \
  -e 'AntCompiler[.]java' -e '/naming/factory/webservices/' -e 'JDTCompiler[.]java' -e 'JspC[.]java' \
  > "$list"
javac -nowarn -encoding ISO-8859-1 -source 1.6 -target 1.6 -d "$destdir" @"$list"
rm -f "$list"
while IFS= read -r resource; do
  rel=${resource#java/}
  mkdir -p "$destdir/$(dirname "$rel")"
  cp "$resource" "$destdir/$rel"
done < <(find java -type f ! -name '*.java')
