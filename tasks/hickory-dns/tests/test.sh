#!/bin/bash
# Verifier entry point. Runs the hidden DNSSEC tests against whatever is in /app
# and writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
#
# Isolation (2026-10-16): the agent shares this container and may have built in
# /opt/harness, /opt/target or /opt/cargo. Nothing from those is trusted here:
# the harness crate is assembled from /tests in a fresh directory, compiled into
# a fresh target directory with a fresh CARGO_HOME whose crate archives are
# checked against the pinned lockfile's checksums. Only /app (the code under
# test) comes from the agent's work.

# Stop the agent before grading (2026-10-16). On an agent timeout Harbor stops waiting for the
# agent but does not kill it inside this shared container, and it was seen editing /app while
# the tests ran (research/own-runs; build/postmortem.py). Kill every Claude Code process first.
for _p in /proc/[0-9]*; do
  case "$(tr '\0' ' ' < "$_p/cmdline" 2>/dev/null)" in
    claude\ *|*/claude\ *|*@anthropic-ai/claude-code*) kill -9 "${_p#/proc/}" 2>/dev/null || true ;;
  esac
done
sleep 1
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

# Build settings that could redirect or skip compilation/execution are not inherited.
unset RUSTFLAGS RUSTDOCFLAGS CARGO_ENCODED_RUSTFLAGS RUSTC RUSTC_WRAPPER RUSTC_WORKSPACE_WRAPPER \
      CARGO_BUILD_RUSTFLAGS CARGO_BUILD_TARGET CARGO_BUILD_TARGET_DIR CARGO_INCREMENTAL \
      RUSTUP_TOOLCHAIN NEXTEST_PROFILE
for _v in $(env | sed -n 's/^\(CARGO_TARGET_[A-Z0-9_]*\)=.*/\1/p; s/^\(NEXTEST_[A-Z0-9_]*\)=.*/\1/p'); do
  unset "$_v"
done
# cargo also reads .cargo/config.toml from every ancestor of the working directory.
rm -rf /.cargo /tmp/.cargo

GRADE="$(mktemp -d /tmp/hickory-grade.XXXXXX)"
# The fresh build tree is ~1 GB; remove it when the script exits (after score.py has
# written reward/results under /logs/verifier). An EXIT trap does not change the exit code.
trap 'rm -rf "$GRADE"' EXIT
export CARGO_HOME="$GRADE/cargo-home"
export CARGO_TARGET_DIR="$GRADE/target"
export CARGO_NET_OFFLINE=true
HARNESS="$GRADE/harness"
mkdir -p "$HARNESS/tests/common" "$HARNESS/.config" "$CARGO_HOME/registry"

# Harness manifest: written here, not taken from /opt/harness.
cat > "$HARNESS/Cargo.toml" <<'TOML'
[package]
name = "hickory-dnssec-harness"
version = "0.0.0"
edition = "2021"
publish = false

[workspace]

[dependencies]
hickory-resolver = { path = "/app/crates/resolver", default-features = false, features = ["dnssec-ring", "tokio"] }
hickory-proto = { path = "/app/crates/proto", default-features = false, features = ["std", "dnssec-ring"] }
test-support = { path = "/app/tests/test-support" }
tokio = { version = "1", features = ["macros", "rt", "rt-multi-thread"] }
futures-util = "0.3"
TOML
# Lockfile: the image's copy, used only if it is byte-identical to the one the image was
# built with (sha256 pinned here). An altered lockfile is not used: no build, reward 0.
LOCK_SHA256=aafc79da14f0ce25c802429bd0f856baa2d36b39f8c5110f4229c83214435013
if [ "$(sha256sum /opt/harness/Cargo.lock 2>/dev/null | cut -d' ' -f1)" = "$LOCK_SHA256" ]; then
    cp /opt/harness/Cargo.lock "$HARNESS/Cargo.lock"
else
    echo "GRADER: /opt/harness/Cargo.lock was modified or removed; refusing to build with it" >&2
fi
printf '[profile.ci.junit]\npath = "junit.xml"\n' > "$HARNESS/.config/nextest.toml"
cp /tests/security/security.rs       "$HARNESS/tests/security.rs"
cp /tests/functional/functional.rs   "$HARNESS/tests/functional.rs"
cp /tests/common/signed_zone.rs      "$HARNESS/tests/common/mod.rs"

# Offline crate cache: copy the registry index and only those crate archives whose
# sha256 matches the pinned lockfile. A missing or altered archive makes the build
# fail (no results -> reward 0) instead of compiling unknown code.
cp -a /opt/cargo/registry/index "$CARGO_HOME/registry/index"
python3 - "$HARNESS/Cargo.lock" /opt/cargo/registry/cache "$CARGO_HOME/registry/cache" <<'PY'
import hashlib, os, re, shutil, sys
lock, src, dst = sys.argv[1:4]
pkgs = re.findall(r'\[\[package\]\]\s*name = "([^"]+)"\s*version = "([^"]+)"\s*source = "registry\+[^"]*"\s*checksum = "([0-9a-f]+)"', open(lock).read())
bad = 0
for idx in os.listdir(src):
    os.makedirs(os.path.join(dst, idx), exist_ok=True)
for name, ver, want in pkgs:
    fn = f"{name}-{ver}.crate"
    for idx in os.listdir(src):
        p = os.path.join(src, idx, fn)
        if os.path.isfile(p):
            if hashlib.sha256(open(p, "rb").read()).hexdigest() == want:
                shutil.copy2(p, os.path.join(dst, idx, fn))
            else:
                bad += 1
                print(f"crate archive does not match the lockfile, not used: {fn}", file=sys.stderr)
print(f"verified {len(pkgs) - bad} of {len(pkgs)} registry crates", file=sys.stderr)
PY

run_group() {
    # $1 = binary/group name (security|functional), $2 = output dir
    local group="$1" outdir="$2"
    # nextest keeps its store (junit.xml) under the harness's own target/ directory.
    rm -rf "$CARGO_TARGET_DIR/nextest" "$HARNESS/target/nextest"
    # --no-fail-fast: every test must run so all cases land in the JUnit report.
    ( cd "$HARNESS" && cargo nextest run --profile ci --offline --locked --no-fail-fast -E "binary(${group})" )
    local junit
    junit="$(find "$HARNESS/target" "$CARGO_TARGET_DIR" -path '*/nextest/ci/junit.xml' -print -quit 2>/dev/null)"
    if [ -n "$junit" ] && [ -f "$junit" ]; then
        cp "$junit" "${outdir}/results.xml"
    fi
}

# --- EDIT: run the two groups. Each writes JUnit XML; a failure in one must not
# --- stop the other (no `set -e`).
run_group security  /logs/verifier/security
run_group functional /logs/verifier/functional

python3 /tests/score.py
