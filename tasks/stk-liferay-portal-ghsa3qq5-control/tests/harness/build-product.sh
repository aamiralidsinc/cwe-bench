#!/usr/bin/env bash
# Verifier-owned compilation of the restored product tree. Installed root-only into
# /opt/liferay/harness before the grading build and run as the unprivileged agent.
set -euo pipefail

cd /workspace

CP=$(ls /opt/liferay/lib/portal/*.jar /opt/liferay/lib/development/*.jar | tr '\n' ':')

rm -rf .classes
mkdir -p .classes

find \
	definitions \
	modules/apps/petra/petra-content/src/main/java \
	modules/apps/petra/petra-encryptor/src/main/java \
	modules/apps/petra/petra-log4j/src/main/java \
	modules/apps/petra/petra-mail/src/main/java \
	modules/apps/petra/petra-portlet-url-builder/src/main/java \
	modules/apps/petra/petra-xml/src/main/java \
	modules/core/petra/petra-concurrent/src/main/java \
	modules/core/petra/petra-executor/src/main/java \
	modules/core/petra/petra-function/src/main/java \
	modules/core/petra/petra-io/src/main/java \
	modules/core/petra/petra-lang/src/main/java \
	modules/core/petra/petra-memory/src/main/java \
	modules/core/petra/petra-nio/src/main/java \
	modules/core/petra/petra-process/src/main/java \
	modules/core/petra/petra-reflect/src/main/java \
	modules/core/petra/petra-sql-dsl-api/src/main/java \
	modules/core/petra/petra-sql-dsl-spi/src/main/java \
	modules/core/petra/petra-string/src/main/java \
	modules/core/petra/petra-url-pattern-mapper/src/main/java \
	modules/core/registry-api/src/main/java \
	portal-impl/src \
	portal-kernel/src \
	portal-test/src \
	support-tomcat/src \
	util-bridges/src \
	util-java/src \
	util-slf4j/src \
	util-taglib/src \
	-name '*.java' 2>/dev/null > .build-srcs.txt

if [ ! -s .build-srcs.txt ]; then
	echo "no Java sources found" >&2

	exit 1
fi

javac -nowarn -proc:none -encoding UTF-8 -source 8 -target 8 \
	-d .classes -cp "$CP" @.build-srcs.txt
