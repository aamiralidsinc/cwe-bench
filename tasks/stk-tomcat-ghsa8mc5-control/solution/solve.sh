#!/bin/bash
# Reference fix: associate the TLS-negotiated host name with the connection, match it against the
# name each request is served under (both protocol front ends and the adapter's served-name
# override), and resolve the protocol host name case-insensitively before selecting the TLS
# configuration. The full source change is in fix.patch.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
