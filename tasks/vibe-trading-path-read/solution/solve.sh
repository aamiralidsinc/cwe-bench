#!/bin/bash
# Reference fix: the published source fix for the agent file tools (document reader, broker-file
# helper, run-workspace tools, pattern scan, backtest) plus the same confinement on the
# factor-analysis inputs and output directory, which the published fix did not cover.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
