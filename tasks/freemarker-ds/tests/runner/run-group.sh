#!/bin/bash
# Runs one hidden group with the JUnit console launcher and writes a single JUnit XML file.
# <group> <xml-output-file>
set -u
GROUP="$1"
OUT_FILE="$2"
WS=/workspace/.htests
JAVA=/usr/local/bin/java
JAVAC=/usr/local/bin/javac
DEPS="$(ls /opt/fm/deps/*.jar | tr '\n' ':')"
CP="$WS/classes:$DEPS"

write_compile_error() {
    mkdir -p "$(dirname "$OUT_FILE")"
    {
        printf '<?xml version="1.0" encoding="UTF-8"?>\n'
        printf '<testsuite name="%s" tests="1" failures="1" errors="0">\n' "$GROUP"
        printf '<testcase classname="verifier.%s.Compilation" name="compiles">\n' "$GROUP"
        printf '<failure message="the hidden %s group did not compile against the submitted sources">%s</failure>\n' \
            "$GROUP" "$1"
        printf '</testcase>\n</testsuite>\n'
    } > "$OUT_FILE"
}

mkdir -p "$WS/$GROUP-classes" "$(dirname "$OUT_FILE")"
SOURCES="$WS/src-$GROUP.txt"
: > "$SOURCES"

if [ "$GROUP" = "security" ]; then
    find "$WS/src/security" -name '*.java' >> "$SOURCES"
else
    find "$WS/src/functional" -name '*.java' >> "$SOURCES"
    find /opt/fm-src/freemarker-test-utils/src/main/java -name '*.java' >> "$SOURCES"
    echo /opt/fm-src/freemarker-core/src/test/java/freemarker/test/MonitoredTemplateLoader.java >> "$SOURCES"
    for t in TemplateCacheTest TemplateNameFormatTest FileTemplateLoaderTest MultiTemplateLoaderTest; do
        echo "/opt/fm-src/freemarker-core/src/test/java/freemarker/cache/$t.java" >> "$SOURCES"
    done
    echo /opt/fm-src/freemarker-core/src/test/java/freemarker/template/TemplateLookupStrategyTest.java >> "$SOURCES"
fi

LOG="$WS/$GROUP-compile.log"
if ! "$JAVAC" -nowarn --release 16 -encoding UTF-8 -cp "$CP" -d "$WS/$GROUP-classes" @"$SOURCES" \
        > "$LOG" 2>&1; then
    write_compile_error "$(tail -c 1500 "$LOG" | tr '\n' ' ' | sed 's/[<&>]/ /g')"
    exit 0
fi

if [ "$GROUP" = "functional" ]; then
    cp -r /opt/fm-src/freemarker-core/src/test/resources/. "$WS/$GROUP-classes/" 2>/dev/null || true
    cp -r /opt/fm-src/freemarker-test-utils/src/main/resources/. "$WS/$GROUP-classes/" 2>/dev/null || true
    SELECT="--select-package verifier.functional"
    for c in freemarker.cache.TemplateCacheTest freemarker.cache.TemplateNameFormatTest \
             freemarker.cache.FileTemplateLoaderTest freemarker.cache.MultiTemplateLoaderTest \
             freemarker.template.TemplateLookupStrategyTest; do
        SELECT="$SELECT --select-class $c"
    done
    TEST_PROPS="-Dfreemarker.test.resourcesDir=$WS/$GROUP-classes"
else
    SELECT="--select-package verifier.security"
    TEST_PROPS=""
fi

TMP_REPORTS="$WS/$GROUP-reports"
rm -rf "$TMP_REPORTS"
mkdir -p "$TMP_REPORTS"
"$JAVA" $TEST_PROPS -jar /opt/fm/deps/junit-platform-console-standalone-1.10.2.jar execute \
    --class-path "$CP:$WS/$GROUP-classes" $SELECT \
    --reports-dir "$TMP_REPORTS" --details=summary --disable-banner \
    > "$WS/$GROUP-run.log" 2>&1
RC=$?

if [ -f "$TMP_REPORTS/TEST-junit-vintage.xml" ]; then
    cp "$TMP_REPORTS/TEST-junit-vintage.xml" "$OUT_FILE"
elif [ -f "$TMP_REPORTS/TEST-junit-jupiter.xml" ]; then
    cp "$TMP_REPORTS/TEST-junit-jupiter.xml" "$OUT_FILE"
else
    write_compile_error "the JUnit launcher produced no report (exit $RC)"
fi
exit 0
