#!/bin/bash
# Compile the library in /app offline, against the vendored sibling jars.
# Prints "library compiled OK" on success. Runs no tests.
set -euo pipefail
CP=/opt/libs/jackson-core-2.18.4.jar:/opt/libs/jackson-annotations-2.18.4.jar
GEN=/tmp/gen/com/fasterxml/jackson/databind/cfg
rm -rf /tmp/gen /tmp/libclasses
mkdir -p "$GEN" /tmp/libclasses

# The build normally generates this tiny version class from an in-repo template.
sed -e 's/@package@/com.fasterxml.jackson.databind.cfg/' \
    -e 's/@projectversion@/2.18.9-SNAPSHOT/' \
    -e 's/@projectgroupid@/com.fasterxml.jackson.core/' \
    -e 's/@projectartifactid@/jackson-databind/' \
    /app/src/main/java/com/fasterxml/jackson/databind/cfg/PackageVersion.java.in \
    > "$GEN/PackageVersion.java"

cd /app
find src/main/java -name '*.java' > /tmp/srcs.txt
echo "$GEN/PackageVersion.java" >> /tmp/srcs.txt
javac -nowarn -proc:none -cp "$CP" -d /tmp/libclasses @/tmp/srcs.txt
echo "library compiled OK"
