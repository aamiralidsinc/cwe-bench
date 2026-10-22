#!/bin/bash
# Reference solution: the published sandbox fix for the image, document and browser
# writers, plus the same confinement for the writers it did not cover (CSV / JSON-to-CSV,
# dedup state, file copy/move, Word image extraction, PDF generation, report writers),
# the files those helpers keep beside a caller-chosen path, and the sibling modules this
# image adds.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
