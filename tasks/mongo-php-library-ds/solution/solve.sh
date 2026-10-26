#!/bin/bash
# Reference fix: validate a database or collection name wherever the library can turn it into
# the namespace the driver/server consumes — handle constructors, the lower-level operation
# constructors, both namespaces of a rename, and the bulk-write and namespace-factory paths —
# while keeping periods inside collection names valid.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
