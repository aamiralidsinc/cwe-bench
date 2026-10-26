#!/bin/bash
# Reference fix: every authoring path that can name a stored credential is checked against the
# caller's read permission on that credential before it is persisted, every one-shot proxy body is
# checked before the credential is resolved, and the check understands every reference form the
# proxy resolves (the proxy's own secret field and a secret named inside a header value). Saved
# proxy requests keep using references that were accepted from an entitled author.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
