#!/bin/bash
# Reference fix: run every expression in the restricted evaluator, guard the property
# name that is actually selected, resolve identifiers by own properties, and apply the
# same guarded read to the path-tracing step that bypassed the evaluator.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
