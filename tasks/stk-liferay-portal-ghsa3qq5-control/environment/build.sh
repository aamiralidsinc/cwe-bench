#!/usr/bin/env bash
# Convenience build for working in this checkout: compile the portal tree this task exercises
# against the jars under /opt/liferay/lib. The grader compiles the same tree with its own copy.
set -euo pipefail

cd "$(dirname "$0")"

CP=$(printf '%s:' /opt/liferay/lib/portal/*.jar /opt/liferay/lib/development/*.jar)

ROOTS=(
	definitions
	modules/apps/petra/petra-content/src/main/java
	modules/apps/petra/petra-encryptor/src/main/java
	modules/apps/petra/petra-log4j/src/main/java
	modules/apps/petra/petra-mail/src/main/java
	modules/apps/petra/petra-portlet-url-builder/src/main/java
	modules/apps/petra/petra-xml/src/main/java
	modules/core/petra/petra-concurrent/src/main/java
	modules/core/petra/petra-executor/src/main/java
	modules/core/petra/petra-function/src/main/java
	modules/core/petra/petra-io/src/main/java
	modules/core/petra/petra-lang/src/main/java
	modules/core/petra/petra-memory/src/main/java
	modules/core/petra/petra-nio/src/main/java
	modules/core/petra/petra-process/src/main/java
	modules/core/petra/petra-reflect/src/main/java
	modules/core/petra/petra-sql-dsl-api/src/main/java
	modules/core/petra/petra-sql-dsl-spi/src/main/java
	modules/core/petra/petra-string/src/main/java
	modules/core/petra/petra-url-pattern-mapper/src/main/java
	modules/core/registry-api/src/main/java
	portal-impl/src
	portal-kernel/src
	portal-test/src
	support-tomcat/src
	util-bridges/src
	util-java/src
	util-slf4j/src
	util-taglib/src
)

: > .build-srcs.txt

for root in "${ROOTS[@]}"; do
	if [ -d "$root" ]; then
		find "$root" -name '*.java' >> .build-srcs.txt
	fi
done

rm -rf .classes
mkdir -p .classes

javac -proc:none -nowarn -encoding UTF-8 -source 8 -target 8 -d .classes -cp "$CP" @.build-srcs.txt

echo "portal compiled into .classes"
