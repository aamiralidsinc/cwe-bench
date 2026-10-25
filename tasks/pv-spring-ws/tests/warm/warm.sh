#!/bin/bash
# Verifier-side preparation. Resolve each module's test runtime classpath once and record
# the resulting external jar list, so the hidden suites build and run with no network.
set -euo pipefail
export HOME=/home/agent

cat > /tmp/verifier-cp.gradle <<'GRADLE'
allprojects { project ->
	project.tasks.register('benchCp') {
		doLast {
			if (project.plugins.hasPlugin('java')) {
				def target = new File('/tmp/bench-cp-' + project.name + '.txt')
				target.text = project.sourceSets.test.runtimeClasspath.files*.absolutePath.join('\n') + '\n'
			}
		}
	}
}
GRADLE

cd /tmp/warm
chmod 755 gradlew
selected=()
for module in spring-ws-core spring-ws-support spring-ws-security spring-ws-test spring-xml; do
	selected+=(":$module:benchCp")
done
./gradlew --no-daemon -I /tmp/verifier-cp.gradle "${selected[@]}"

for part in /tmp/bench-cp-*.txt; do cat "$part"; echo; done \
	| grep -v '^/tmp/warm' | grep -v '^$' | sort -u | paste -sd: - | tr -d '\n' > /tmp/bench-classpath.txt
chmod a+r /tmp/bench-classpath.txt
cd /
rm -rf /tmp/warm /tmp/bench-cp-*.txt /tmp/verifier-cp.gradle
