#!/bin/bash
# Reference fix: decide sensitivity after resolving a team scoped spelling of an
# option back to the registered option, everywhere values are hidden or masked,
# and register every team scoped secret with the start-up log masker.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
