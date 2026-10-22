#!/bin/bash
# Reference fix: keep credential material out of administrator-facing account
# responses and apply the role-hierarchy guard to every administrative action
# on another account.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
