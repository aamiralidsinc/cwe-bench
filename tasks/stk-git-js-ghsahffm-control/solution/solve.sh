#!/bin/bash
# Reference fix: read every configuration assignment (short/long switches and the config-writing
# subcommand), resolve included configuration sources before deciding, and refuse remote pack
# commands on every operation. The existing opt-in and data-carrying config keep working.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
