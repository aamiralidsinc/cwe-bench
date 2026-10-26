#!/bin/bash
# Reference fix: refuse requests that only passed because the resource is publicly readable on
# every entry point that can change data belonging to it, while leaving member triage and public
# reads untouched.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
