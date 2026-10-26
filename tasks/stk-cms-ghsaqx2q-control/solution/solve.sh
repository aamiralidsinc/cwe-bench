#!/bin/bash
# Control reference fix: remove behavior and event-handler wiring from the decoded field-layout
# definition before it is turned into layout objects.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
