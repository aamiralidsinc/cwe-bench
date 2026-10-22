#!/bin/bash
# Reference fix: when the instance setting requires user credentials, every
# affected scaffolder action (GitHub, GitLab, the built-in fetch actions and the
# cookiecutter/rails fetch steps) refuses to act without a non-empty user
# credential and never falls back to the backend integration credential. With the
# setting off or absent, the previous behaviour is unchanged.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
