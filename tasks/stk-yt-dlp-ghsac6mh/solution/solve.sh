#!/bin/bash
# Reference fix: give the extension-changing helpers and the output-template name the same
# file-type policy, keep shortcut types to the link feature, and stop a lone dot component
# from being used as a path element.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
