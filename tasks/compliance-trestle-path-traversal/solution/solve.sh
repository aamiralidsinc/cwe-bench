#!/bin/bash
# Reference solution: the upstream source fix plus the same workspace check on the
# routes it did not cover (import, models saved by name, component markdown overwrite).
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
