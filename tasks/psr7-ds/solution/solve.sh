#!/bin/bash
# Reference fix: every host the library records must be a single well-formed
# authority host, no matter which entry point supplied it.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
