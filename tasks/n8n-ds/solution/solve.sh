#!/bin/bash
# Reference fix: every message value that reaches a mail transport is rendered as
# text instead of being handed over as a content reference, the host-side template
# and remote-image producers no longer read or fetch by workflow value, a path/URL
# attachment source is no longer accepted, and the transports refuse file/URL content.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
