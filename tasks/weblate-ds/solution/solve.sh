#!/bin/bash
# Reference fix: the published source changes for the hidden-content lookups, the
# access-scoped machinery routes, the corrected cached project filter, and the task's
# additional endpoints.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
