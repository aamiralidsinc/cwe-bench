#!/bin/bash
# Reference fix: every local-API call made for a request runs under the requesting user's
# access (single-image read and save, batch read and per-locale writes, and the injected
# gap-filling, export and import routes); the shared health scan stays elevated and complete,
# and both of its consumers filter the cached result per request by collection read access.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
