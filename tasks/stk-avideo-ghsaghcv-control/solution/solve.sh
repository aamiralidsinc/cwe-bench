#!/bin/bash
# Control reference fix: decide provenance from the connection token the server issued and
# recursively remove the executable field from a client-supplied frame; frames the platform's
# own server code produced keep their payload untouched.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
