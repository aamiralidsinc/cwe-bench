#!/bin/bash
# Build the submitted product sources with the pre-resolved, offline dependency classpath.
set -uo pipefail
cd /workspace || exit 1
rm -rf .htests/product .htests/srcs.txt
mkdir -p .htests/product || exit 1
CP=$(cat /opt/bench-classpath.txt) || exit 1
find spring-xml/src/main/java spring-ws-core/src/main/java spring-ws-support/src/main/java \
     spring-ws-security/src/main/java spring-ws-test/src/main/java -name '*.java' > .htests/srcs.txt
if ! javac -nowarn -encoding UTF-8 --release 17 -cp "$CP" -d .htests/product @.htests/srcs.txt; then
	echo "product sources did not compile" >&2
	exit 1
fi
for m in spring-xml spring-ws-core spring-ws-support spring-ws-security spring-ws-test; do
	if [ -d "$m/src/main/resources" ]; then
		cp -r "$m/src/main/resources/." .htests/product/
	fi
done
exit 0
