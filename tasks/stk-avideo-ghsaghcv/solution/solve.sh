#!/bin/bash
# Reference fix: decide provenance from the connection token the server issued, then remove
# executable fields from every carrier of a client-supplied frame, accept only a plain
# application-function name, and overwrite the sender identity fields with the token's owner.
# Server-issued frames keep their payload untouched. The client script resolves the function by
# property lookup instead of building and running a code string.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
