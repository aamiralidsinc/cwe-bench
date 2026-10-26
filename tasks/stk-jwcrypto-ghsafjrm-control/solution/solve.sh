#!/bin/bash
# Reference fix: bound how much plaintext one decryption call can inflate, refuse a compressed
# payload before leaving it on the object, stop after the first recipient that decrypts, and
# accept a compression declaration only from the authentication-protected header.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
