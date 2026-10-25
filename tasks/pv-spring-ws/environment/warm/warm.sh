#!/bin/bash
# Warm the Gradle dependency cache, then verify the project's affected tests.
set -euo pipefail
export HOME=/home/agent
cd /workspace
chmod +x gradlew
./gradlew --no-daemon -I /tmp/collect.gradle \
	:spring-ws-core:benchPrintClasspath :spring-ws-support:benchPrintClasspath \
	:spring-ws-security:benchPrintClasspath :spring-ws-test:benchPrintClasspath \
	:spring-xml:benchPrintClasspath \
	:spring-ws-support:testClasses :spring-ws-security:testClasses
./gradlew --no-daemon :spring-ws-core:test --tests 'org.springframework.ws.soap.addressing.server.*'
rm -f /tmp/bench-cp-*.txt
