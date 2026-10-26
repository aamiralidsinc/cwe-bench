#!/bin/bash
# Reference fix: render every application-supplied name and string value in a
# position that cannot change the structure of the compiled statement.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
