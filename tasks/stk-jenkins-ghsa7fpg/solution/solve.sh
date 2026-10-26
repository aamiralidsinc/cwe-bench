#!/bin/bash
# Reference fix: judge the build-other-projects data that is about to be stored against the
# acting user's build permission, at every point where a job's configuration is written.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
