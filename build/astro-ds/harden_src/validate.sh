#!/bin/bash
# Validate each variant: fresh pinned+injection, apply variant, rebuild, run both groups.
set -u
cd /app || exit 1
PKG=/app/packages/astro
run_variant() {
  local name="$1" patchfile="$2"
  git checkout -q -- . || return 1
  find packages/astro/src -name '*.orig' -delete 2>/dev/null
  find packages/astro/src -name '*.rej' -delete 2>/dev/null
  rm -rf packages/astro/src/actions/form-handler.ts \
         packages/astro/src/core/app/origin-check.ts \
         packages/astro/src/core/endpoints \
         packages/astro/src/core/pages/partial-handler.ts \
         packages/astro/src/core/pages/fragment-handler.ts \
         packages/astro/src/core/rewrites/rewrite-handler.ts
  patch -p1 -s < /tmp/injection_new.patch || { echo "$name INJECT_FAIL"; return 1; }
  if [ -n "$patchfile" ]; then
    patch -p1 -s < "$patchfile" || { echo "$name PATCH_FAIL"; return 1; }
  fi
  ( cd /app && pnpm --filter astro run build:ci ) >/tmp/build-$name.log 2>&1 || {
    echo "$name BUILD_FAIL"; return 1; }
  local sec fun
  ( cd "$PKG" && NO_COLOR=1 FORCE_COLOR=0 node --test --test-concurrency=1 --test-timeout=120000 \
      test-hidden/units/security/*.test.ts ) >/tmp/sec-$name.log 2>&1
  ( cd "$PKG" && NO_COLOR=1 FORCE_COLOR=0 node --test --test-concurrency=1 --test-timeout=120000 \
      test-hidden/units/functional/*.test.ts test-hidden/units/hono/*.test.ts \
      test-hidden/units/fetch/*.test.ts test-hidden/units/actions/*.test.ts \
      test-hidden/units/middleware/*.test.ts ) >/tmp/fun-$name.log 2>&1
  sec=$(grep -E "pass [0-9]+|fail [0-9]+" /tmp/sec-$name.log | head -2 | tr '\n' ' ')
  fun=$(grep -E "pass [0-9]+|fail [0-9]+" /tmp/fun-$name.log | head -2 | tr '\n' ' ')
  echo "$name | sec: $sec | fun: $fun"
}

run_variant nop ""
run_variant fix /tmp/out/fix_new.patch
run_variant sf_miss_fragments /tmp/out/sf_miss_fragments.patch
run_variant sf_miss_rewrites /tmp/out/sf_miss_rewrites.patch
run_variant pass_hardening /tmp/out/pass_hardening_new.patch
run_variant pass_alt /tmp/out/pass_alt_fetch_primitives_new.patch
run_variant blind /tmp/out/blind_new.patch
