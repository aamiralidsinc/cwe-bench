#!/bin/bash
# Reference fix: apply the set's type decision to the stored name (after sanitising and
# lowercasing the explicit name), refuse a refused type in any dot-separated part, and keep
# the resolved write inside the configured destination.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
