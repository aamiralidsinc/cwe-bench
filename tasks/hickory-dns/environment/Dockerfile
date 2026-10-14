FROM rust:1-slim-bookworm

# Tools the project build, the reference-fix patch step, and the verifier need.
# Everything is installed here so the task runs with NO network afterwards.
# gcc/libc6-dev/make are required to compile the `ring` crypto crate.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git patch bash gcc libc6-dev make \
    && rm -rf /var/lib/apt/lists/*

# Fetch the repository at the VULNERABLE parent commit into /app, then delete
# the git history so later (fixed) commits are not present in the image.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/hickory-dns/hickory-dns \
    && git fetch -q --depth 1 origin 5213becf46316a6c16f2ddf4d904f52c5502efdc \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Shared cargo caches: CARGO_HOME holds the crate registry, CARGO_TARGET_DIR the
# compiled artifacts. Both are baked into the image so a verifier run neither
# fetches from the network nor recompiles the dependency world.
ENV CARGO_HOME=/opt/cargo \
    CARGO_TARGET_DIR=/opt/target \
    PATH=/opt/cargo/bin:/usr/local/bin:$PATH

# Test runner that emits JUnit XML. Build-time only (needs network here).
# Pick the binary for the image's architecture (arm64 here, amd64 elsewhere).
RUN set -eux; \
    case "$(uname -m)" in \
      aarch64|arm64) url=https://get.nexte.st/latest/linux-arm ;; \
      x86_64|amd64)  url=https://get.nexte.st/latest/linux ;; \
      *) echo "unsupported arch $(uname -m)" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "$url" -o /tmp/nextest.tar.gz; \
    tar -xzf /tmp/nextest.tar.gz -C /usr/local/bin; \
    rm /tmp/nextest.tar.gz; \
    cargo nextest --version

# The DNSSEC verification harness: a standalone crate that drives the resolver's
# public API against a scripted, in-process upstream (no real DNS, no sockets).
COPY harness /opt/harness

# Pre-build the entire dependency closure AND the hickory crates at the
# vulnerable commit, so a verifier run only recompiles whatever /app source the
# solver actually changed. The test binaries are compiled but not run here.
RUN cd /opt/harness && cargo nextest run --profile ci --no-run

# python3 runs the verifier's scorer (tests/score.py). Added after the prewarm
# so changing it never invalidates the expensive compile layer.
RUN apt-get update && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
