#!/usr/bin/env bash
# Apply the reference fix to the workspace.
set -eu
cd /workspace
git apply /solution/fix.patch
