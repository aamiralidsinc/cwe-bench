#!/bin/bash
# Reference fix: refuse empty key material at every point where it can enter or be used,
# and refuse empty plain secrets before they are turned into key material.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
