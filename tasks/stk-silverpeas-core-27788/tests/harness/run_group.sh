#!/bin/bash
# Compile one hidden group against the product classes built from the submitted tree and run it,
# always leaving a JUnit XML file behind (a compile or start-up failure is a failing group).
set -u
G=$1
OUT=$2
S=/workspace/.htests
W=$S/work-$G
C=$S/config-$G
D=$S/classes-$G

failxml() {
  {
    printf '<?xml version="1.0" encoding="UTF-8"?>\n'
    printf '<testsuite name="security-fix" tests="1" failures="1" errors="0" skipped="0">\n'
    printf ' <testcase classname="silverpeas.hidden.%s" name="group">\n' "$G"
    printf '  <failure message="%s">%s</failure>\n' "$1" "$1"
    printf ' </testcase>\n</testsuite>\n'
  } > "$OUT"
}

JAVA_HOME="${JAVA_HOME:-/opt/java/openjdk}"
if [ ! -x "$JAVA_HOME/bin/java" ]; then
  JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")"
fi
JAVA="$JAVA_HOME/bin/java"
JAVAC="$JAVA_HOME/bin/javac"
export JAVA_HOME

# ---- fixture configuration: the product reads its settings and bundles from this directory ----
rm -rf "$W" "$C" "$D"
mkdir -p "$W/uploads" "$W/temp" "$W/outside" "$D"
mkdir -p "$C/org/silverpeas/lookAndFeel" "$C/org/silverpeas/util/uploads" \
         "$C/org/silverpeas/util/peasUtil/multiLang" "$C/org/silverpeas/util/logging" \
         "$C/META-INF/services"

cat > "$C/maven.properties" <<EOF
test.resources.directory=$C
project.build.directory=$W/build
EOF

cat > "$C/org/silverpeas/general.properties" <<EOF
ApplicationURL=/silverpeas/
uploadsPath=$W/uploads
tempPath=$W/temp
securityPath=$W/security
sessionTimeout=/admin/jsp/SessionTimeout.jsp
accessForbidden=/admin/jsp/accessForbidden.jsp
redirectAppInMaintenance=/admin/jsp/appInMaintenance.jsp
RepositoryTypeTemp=Temp
advancedSearchWithPDC=true
domainVisibility=0
httpServerBase=
webdav.workspace=jackrabbit
webdav.repository=repository
removeLocksOnInit=yes
EOF

cat > "$C/org/silverpeas/lookAndFeel/generalLook.properties" <<EOF
loginPage=
defaultStyleSheet=
image.size.thumbnail=100x100
EOF

cat > "$C/org/silverpeas/util/uploads/uploadSettings.properties" <<EOF
FileIconsPath=/silverpeas/icons/
unknown=unknown.gif
FileSizeReference=1
DownloadTime=1
EOF

cat > "$C/org/silverpeas/util/peasUtil/multiLang/fileServerBundle.properties" <<EOF
warning=The requested file is not available.
EOF

printf 'namespace=silverpeas\nlevel=INFO\n' \
  > "$C/org/silverpeas/util/logging/silverpeasLogging.properties"
printf 'namespace=silverpeas.core\n' \
  > "$C/org/silverpeas/util/logging/silverpeasCoreLogging.properties"

printf 'org.silverpeas.kernel.test.TestBeanContainer\n' \
  > "$C/META-INF/services/org.silverpeas.kernel.BeanContainer"
printf 'org.silverpeas.kernel.test.TestResourcesLocation\n' \
  > "$C/META-INF/services/org.silverpeas.kernel.SilverpeasResourcesLocation"

# ---- classpath: freshly built product classes first, then the warmed dependency jars ----------
if [ -f /opt/sp-cp.txt ]; then
  DEPS=$(cat /opt/sp-cp.txt)
else
  DEPS=""
fi
CP="$C"
for d in core-war core-library core-web core-rs core-api core-jcr core-test core-services/chat \
         core-services/silverstatistics; do
  [ -d "/workspace/$d/target/classes" ] && CP="$CP:/workspace/$d/target/classes"
done
CP="$CP:$DEPS"

if ! "$JAVAC" -nowarn -cp "$CP" -d "$D" "$S"/harness/*.java "$S"/$G/*.java \
     > "$S/javac-$G.log" 2>&1; then
  failxml "the group could not be compiled against the submitted code"
  tail -60 "$S/javac-$G.log"
  exit 0
fi

CLASSES=""
for f in "$S"/$G/*.java; do
  CLASSES="$CLASSES silverpeas.hidden.$(basename "$f" .java)"
done

cd /workspace || exit 0
"$JAVA" -Dhidden.work="$W" -cp "$C:$D:$CP" silverpeas.hidden.JUnitXmlRunner "$OUT" $CLASSES \
  > "$S/run-$G.log" 2>&1
rc=$?
cat "$S/run-$G.log"
[ -s "$OUT" ] || failxml "the group produced no results (exit $rc)"
exit 0
