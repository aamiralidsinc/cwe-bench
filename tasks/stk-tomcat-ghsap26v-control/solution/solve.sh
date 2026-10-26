#!/bin/bash
# Reference solution for the control task: the advisory's own route only.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
