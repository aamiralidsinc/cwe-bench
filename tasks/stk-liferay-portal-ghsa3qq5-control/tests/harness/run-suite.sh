#!/usr/bin/env bash
# Compile and run one hidden group against the agent's compiled tree, writing JUnit XML.
# Usage: run-suite.sh <security|functional> <output.xml>
set -u

group="$1"
out="$2"

CP=$(ls /opt/liferay/lib/portal/*.jar /opt/liferay/lib/development/*.jar | tr '\n' ':')

base=/workspace/.htests
src="$base/src"
classes="$base/$group-classes"

rm -rf "$classes"
mkdir -p "$classes"

if [ "$group" = "security" ]; then
	src_dirs="$src/support $src/security"
	test_classes="com.liferay.bench.EscapeRedirectBypassSecurityTest"
else
	src_dirs="$src/support $src/functional"
	test_classes="com.liferay.bench.RelativeRedirectFunctionalTest com.liferay.portal.util.ProjectPortalImplEscapeRedirectTest"
fi

find $src_dirs -name '*.java' > "$base/$group-srcs.txt" 2>/dev/null

if javac -nowarn -proc:none -encoding UTF-8 -d "$classes" \
		-cp "/workspace/.classes:$CP" @"$base/$group-srcs.txt" \
		> "$base/$group-javac.log" 2>&1; then

	java -cp "$classes:/workspace/.classes:/opt/liferay/resources:$CP" \
		com.liferay.bench.JUnitXmlRunner "$out" $test_classes
	exit $?
fi

# A submission that no longer offers the API the suites compile against scores zero; it is not a
# verifier defect, so still produce a result the scorer can read.
{
	printf '<?xml version="1.0" encoding="UTF-8"?>\n'
	printf '<testsuite name="%s" tests="1" failures="0" errors="1" skipped="0">\n' "$group"
	printf ' <testcase classname="compile" name="compile">'
	printf '<error message="the hidden suites do not compile against this submission">'
	tail -20 "$base/$group-javac.log" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g'
	printf '</error></testcase>\n'
	printf '</testsuite>\n'
} > "$out"

exit 0
