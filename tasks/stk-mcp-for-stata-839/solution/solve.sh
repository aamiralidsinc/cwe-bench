#!/bin/bash
# Reference fix: every caller-supplied value is checked against the Stata command it will be
# embedded in before the command text is built, so it cannot become command syntax.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
