#!/bin/bash
# Reference fix: make every email-link builder use the installation's configured
# public URL, and reject (or avoid) hosts that are not trusted.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
