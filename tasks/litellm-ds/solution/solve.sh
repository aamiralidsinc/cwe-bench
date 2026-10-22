#!/bin/bash
# Reference fix: enforce the request-parameter/destination rule at every place
# a caller can select an outbound destination (body, deployment path, multipart
# bracket-notation form for every nested container, the queue route, the
# moderation route) and stop configured credentials or stored-credential
# references from following a caller-chosen destination in the connectivity test.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
