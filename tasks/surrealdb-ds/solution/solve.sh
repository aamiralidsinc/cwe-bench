#!/bin/bash
# Reference fix: stored conditions and permission clauses cannot modify data,
# at definition time and while the engine evaluates them, without changing
# the writes that definitions are themselves meant to perform.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
