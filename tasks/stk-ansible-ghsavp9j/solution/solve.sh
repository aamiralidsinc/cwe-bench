#!/bin/bash
# Reference fix: keep the decrypted working copy in a private location and on the descriptor the
# process created, destroy it on every exit (including a failed save), and destroy the temporary
# copy created by the second decryption path.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
