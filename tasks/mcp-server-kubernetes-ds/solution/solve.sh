#!/bin/bash
# Reference fix: one guard over the fully constructed argv (long and short
# option spellings, attached values, end-of-options), installed on every path
# that starts kubectl or helm -- the structured tools, the chart tool, the
# long-running port-forward and follow-mode executors, and the raw resource
# read.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
