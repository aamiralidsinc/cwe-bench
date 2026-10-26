#!/bin/bash
# Reference fix: a class reference carried by a model's stored configuration may only be
# imported when the load explicitly allows untrusted code; keep the legitimate reloads.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
