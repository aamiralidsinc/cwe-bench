#!/usr/bin/env bash
# Compile the library modules this task exercises with the local JDK. The project's Gradle build
# resolves its plugins from the network, so the modules are compiled directly instead.
set -e
cd "$(dirname "$0")"
rm -rf build/classes
mkdir -p build/classes
find core/src/main/java prov/src/main/java util/src/main/java pkix/src/main/java -name '*.java' > build/sources.txt
javac -nowarn -encoding UTF-8 -d build/classes @build/sources.txt
for m in core prov util pkix; do
    if [ -d "$m/src/main/resources" ]; then
        cp -a "$m/src/main/resources/." build/classes/
    fi
done
echo "compiled $(find build/classes -name '*.class' | wc -l) classes"
