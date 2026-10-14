FROM rust:1.91-slim-bookworm

# Tools the task and verifier need. Everything is installed now so the trial
# itself needs NO network.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git patch bash python3 pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Fetch the library at the VULNERABLE parent commit, then drop the history so
# the later fix is not present in the image.
WORKDIR /app
RUN git init -q . \
 && git remote add origin https://github.com/eugeny/russh \
 && git fetch -q --depth 1 origin 3430fd26ecafc0dc3705210f5f39a9119fa22774 \
 && git checkout -q FETCH_HEAD \
 && rm -rf /app/.git

# Hidden test harness: a standalone crate that drives russh's public
# client/server transport API (path dependency on /app/russh). The agent can
# only edit /app, never /opt/harness.
ENV CARGO_TERM_COLOR=never
WORKDIR /opt/harness

# 1) Dependency-cache layer: compile russh (from /app at the vulnerable commit)
#    and every dependency against stub sources, so an agent's later edit to
#    /app/russh recompiles only russh, not the whole dependency graph.
COPY harness/Cargo.toml ./Cargo.toml
RUN mkdir -p src tests && : > src/lib.rs && : > tests/security.rs && : > tests/functional.rs \
 && cargo build --tests 2>&1 | tail -5

# 2) Real harness sources, and pre-build the test binaries so the gate does not
#    recompile them on every run. touch so the real sources are newer than the
#    stub-built artifacts (otherwise cargo skips rebuilding them).
COPY harness ./
RUN touch src/lib.rs tests/*.rs && cargo build --tests 2>&1 | tail -20

# Offline JUnit-emitting test runner (cargo-nextest), installed after the
# compile layers so it never invalidates them. Arch-aware; vendored into the
# image so the verifier runs without network.
RUN set -eu; case "$(uname -m)" in \
      x86_64)        url=https://get.nexte.st/latest/linux ;; \
      aarch64|arm64) url=https://get.nexte.st/latest/linux-arm ;; \
      *) echo "unsupported arch $(uname -m)"; exit 1 ;; \
    esac; curl -LsSf "$url" | tar zxf - -C /usr/local/bin && cargo-nextest --version

WORKDIR /app

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
