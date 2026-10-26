#!/bin/bash
# Reference fix: prevent a configuration reader who may not configure an object from receiving
# the secret values recorded in that object's configuration history, in every output the history
# feature offers, while configuring users and restores keep the raw values.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
