#!/bin/bash
# Reference solution: the upstream source fix plus the same workspace check on the
# routes and companion outputs it did not cover (external model import, models saved
# by name, component markdown overwrite, inheritance view and assembled output names).
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
