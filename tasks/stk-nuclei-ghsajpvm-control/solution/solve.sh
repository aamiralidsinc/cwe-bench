#!/bin/bash
# Reference fix: render authored template text once and keep every value that
# came from the target as terminal data in all evaluation paths.
set -euo pipefail
cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
