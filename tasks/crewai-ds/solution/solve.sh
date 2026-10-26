#!/bin/bash
# Reference fix: decide every remote read by validating each destination (the address the caller
# gives and every address reached while satisfying the read) before a request is sent, and send
# credentials only to the origin they were meant for.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
