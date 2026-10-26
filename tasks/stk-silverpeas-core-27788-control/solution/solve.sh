#!/bin/bash
# Reference fix for the control: close the reported download route only.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
