#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
if [ "$(cat /app/hello.txt 2>/dev/null)" = "hello harbor" ]; then reward=1; else reward=0; fi
echo "$reward" > /logs/verifier/reward.txt
printf '{"reward": %s}\n' "$reward" > /logs/verifier/reward.json
exit $((reward == 1 ? 0 : 1))
