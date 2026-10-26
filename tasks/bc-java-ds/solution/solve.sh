#!/usr/bin/env bash
# Reference fix: judge every name a certificate carries, and every constraint a CA publishes, on
# the name it denotes rather than on the characters used to spell it.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
