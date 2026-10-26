#!/bin/bash
# Reference fix for the reported route. Style content is validated as one stylesheet before a
# single cleaned child is serialised.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
