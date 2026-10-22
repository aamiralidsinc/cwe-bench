#!/bin/bash
# Reference fix: decide image-storage writes by the contents of the file at every
# ingestion boundary, sanitize and keep vector images, and stop the archive's
# generic content-file handler from keeping a second copy of a rejected image.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
