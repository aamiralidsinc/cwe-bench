#!/bin/bash
# Reference fix: remove behavior and event-handler wiring from every configuration path that is
# turned into layout or query objects — the decoded request layout, the JSON-string form of a
# tab's element list, the project-config model factory, and element-index source definitions.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
