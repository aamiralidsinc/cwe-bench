# Rust 1.88 matches the project's declared MSRV (edition 2024).
FROM rust:1.88-bookworm

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the client at the pinned (vulnerable) commit.
ARG REPO_URL=https://github.com/hubuum/hubuum-client-rust
ARG COMMIT=9c123207eb141ef1cfc8f53af538a06eeb458461
RUN git init -q . \
    && git remote add origin "${REPO_URL}.git" \
    && git fetch -q --depth 1 origin "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# Apply the task's sibling additions, then drop the git history so no later
# (fixed) commit, tag or branch is present in the image.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /app/.git

# Resolve and compile the project and its test toolchain while the network is
# still available; grading runs offline.
RUN cargo fetch --locked
RUN cargo test --no-run --locked --features blocking
RUN cargo test --no-run --locked --features blocking,typed-schemas --lib
RUN cargo test --no-run --locked --features blocking,typed-schemas --test foundations

ENV CARGO_NET_OFFLINE=true

# Defensive guard: drop any text file naming the advisory. The checkout predates
# the fix, so this finds nothing today.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-2625-RW7M-5Q5X|CVE-2026' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
