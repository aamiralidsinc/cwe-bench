#!/bin/bash
# Reference fix: no workspace value may resolve outside the disk's mount point. The published
# check is applied to the custom path and to the workspace pattern after macro expansion, a
# recorded allocation is re-checked when a later build reuses it, and the two controller-side
# actions that turn a recorded path into a filesystem location (browsing and cleanup) confine
# the resolved location to the mount point. The job-supplied sub-folder of the default path is
# validated the same way.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
