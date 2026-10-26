#!/bin/bash
# Control reference: the advisory's own route only. A refused WebSocket mount
# sends the navigate frame, clears the view and terminates the transport.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
