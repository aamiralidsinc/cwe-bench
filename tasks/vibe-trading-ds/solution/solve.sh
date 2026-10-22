#!/bin/bash
# Reference fix: the published source fix for the agent file tools (document reader, broker-file
# helper, run-workspace tools, pattern scan, backtest) plus the same confinement on the
# factor-analysis inputs and output directory, the stored-document preview route, the data file
# named by a run's config, a skill's supporting-file lookup, the run routes that build a path
# from a route identifier, and the journal location recorded with a shadow profile.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
