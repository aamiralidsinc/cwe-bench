#!/bin/bash
# Hidden TypeScript suites for the core package, run as the unprivileged `agent`
# user. usage: run_ts.sh <security|functional> <junit-output>
set -u

group="$1"
out="$2"
cd /workspace/runtime/typescript || exit 1
pkg=/workspace/runtime/typescript/packages/core

# Never trust module trees inside the restored workspace: drop any the agent
# created so resolution goes through the pristine cache bound at the root.
for d in /workspace/runtime/typescript/packages/*/node_modules; do
  [ -e "$d" ] && rm -rf "$d"
done
if [ ! -e /workspace/runtime/typescript/node_modules ]; then
  ln -s /opt/prompty-ts/node_modules /workspace/runtime/typescript/node_modules || exit 1
fi

rm -rf "$pkg/_verifier"
mkdir -p "$pkg/_verifier"
cp /workspace/.htests/"$group"/*.test.ts "$pkg/_verifier"/ 2>/dev/null || exit 1
cp /workspace/.htests/runner/vitest.config.mjs "$pkg/_verifier.config.mjs" || exit 1

/opt/prompty-ts/node_modules/.bin/vitest run \
  --root "$pkg" \
  --config "$pkg/_verifier.config.mjs" \
  --reporter=junit \
  --outputFile="$out"
