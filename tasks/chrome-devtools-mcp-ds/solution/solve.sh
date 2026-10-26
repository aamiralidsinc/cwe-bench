#!/bin/bash
# Reference fix: resolve every path to the real location the filesystem would use — including
# links whose target does not exist yet — and compare it with the canonical roots. Applied to
# the shared check, to the actual name each writer produces, to the reload path, and to the
# reusable summary file kept beside a snapshot, while the coupled legitimate behaviours (new
# files, linked roots, unresolved roots, temporary output, in-workspace links) keep working.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
