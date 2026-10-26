#!/usr/bin/env bash
# Reference solution for the control task (the advisory's own routes): bound the decoded size of a
# compressed workbook, and add a per-chain visited-block guard to each of the four sector-chain
# walks in the shared container parser.
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
