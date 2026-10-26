#!/bin/bash
# Reference fix: every public surface that deserializes a caller-named artifact refuses
# unless the caller vouched for its source, and the decision is taken before the file is
# opened. The compatibility repair and envelope-less artifacts keep working when vouched.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
