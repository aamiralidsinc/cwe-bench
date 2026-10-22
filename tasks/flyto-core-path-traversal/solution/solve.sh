#!/bin/bash
# Reference solution: the upstream source fix (every file-writing module it confines to the
# operator's sandbox) plus the same sandbox check on the writers it did not cover
# (CSV/JSON-to-CSV writers, PDF generation, Word image extraction, file copy/move).
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
