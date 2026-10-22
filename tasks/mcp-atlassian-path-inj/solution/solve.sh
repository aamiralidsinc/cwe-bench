#!/bin/bash
# Reference fix: confine every caller-supplied local file path that the server
# reads and sends to Atlassian — attachment uploads (single, list, create- and
# update-issue) and page/issue/comment bodies read from a file — to the current
# working directory (workspace), resolving symlinks and comparing on the
# resolved path, on every one of those routes. In-memory (base64) uploads and
# inline bodies are unaffected.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
