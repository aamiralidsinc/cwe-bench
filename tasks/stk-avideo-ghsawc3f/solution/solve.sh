#!/bin/bash
# Reference fix: make the media-command sanitizer quote-aware and stop trusting the shell
# wrapper, then escape or restrict the other values that reach the same command lines.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
