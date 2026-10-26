#!/bin/bash
# Reference fix: a mount that does not complete (refused by the view's
# authorisation, diverted by a mount-time hook, or left undecidable because the
# check failed) must not stay the session's event target, on either mount
# implementation, and a single refused mount terminates the transport.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
