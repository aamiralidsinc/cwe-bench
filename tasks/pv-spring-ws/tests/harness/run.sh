#!/bin/bash
# Compile and run one hidden suite, writing a single JUnit XML report to the given path.
set -u
group=$1
out=$2

emit_failure() {
	printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?>' \
		"<testsuite name=\"wsbench.$group\" tests=\"1\" failures=\"1\" errors=\"0\" skipped=\"0\">" \
		"  <testcase classname=\"wsbench.$group.Submission\" name=\"suiteExecutes\"><failure message=\"$1\">$1</failure></testcase>" \
		'</testsuite>' > "$out"
}

cd /workspace || { emit_failure "workspace missing"; exit 0; }
CP=$(cat /opt/bench-classpath.txt) || { emit_failure "classpath missing"; exit 0; }
CONSOLE=/workspace/.htests/junit-console.jar
CLASSES="/workspace/.htests/classes-$group"
REPORT="/workspace/.htests/report-$group"
rm -rf "$CLASSES" "$REPORT"
mkdir -p "$CLASSES" "$REPORT" || { emit_failure "work dir unavailable"; exit 0; }

SOURCES=$(find "/workspace/.htests/$group" /workspace/.htests/support -name '*.java')
if ! javac -nowarn -encoding UTF-8 --release 17 -cp "$CP:/workspace/.htests/product" -d "$CLASSES" $SOURCES; then
	emit_failure "suite did not compile"
	exit 0
fi

java -jar "$CONSOLE" --class-path "$CP:/workspace/.htests/product:$CLASSES" \
	--scan-class-path "$CLASSES" --reports-dir "$REPORT" --disable-banner --details=summary \
	> "/workspace/.htests/$group.log" 2>&1

if [ -f "$REPORT/TEST-junit-jupiter.xml" ]; then
	cp "$REPORT/TEST-junit-jupiter.xml" "$out"
else
	emit_failure "suite produced no report"
fi
exit 0
