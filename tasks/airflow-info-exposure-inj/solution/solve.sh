#!/bin/bash
# Reference fix: decide sensitivity after resolving a team scoped spelling of an
# option back to the registered option, everywhere values are hidden or masked.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
