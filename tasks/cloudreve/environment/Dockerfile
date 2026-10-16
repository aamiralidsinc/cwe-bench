# Cloudreve v4 is a Go project (module github.com/cloudreve/Cloudreve/v4).
# Everything is installed here so the task runs with NO network after build.
FROM golang:1.26-bookworm

# Tools needed by the project build, the reference-fix patch step and the
# verifier (which drives the running server over HTTP from Python).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git patch bash python3 \
    && rm -rf /var/lib/apt/lists/*

# Pure-Go build: the sqlite driver is modernc.org/sqlite and the tree has no
# cgo, so CGO_ENABLED=0 keeps the image lean and avoids a C toolchain.
# GOTOOLCHAIN=local pins the toolchain to this image's Go. The module/build
# caches ($GOPATH/pkg/mod, /root/.cache/go-build) are baked into the image, so
# a verifier rebuild from /app is incremental and never touches the network.
ENV GOTOOLCHAIN=local \
    CGO_ENABLED=0 \
    GOFLAGS=-mod=mod

# Fetch the repository at the VULNERABLE commit C into /app, then drop the git
# history so later (fixed) commits are not present in the image.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/cloudreve/cloudreve \
    && git fetch -q --depth 1 origin 54dc81deefcd799300119d0b9bc19c935a0881b5 \
    && git checkout -q FETCH_HEAD

# The frontend is a separate build embedded via //go:embed assets.zip. We serve
# the API only, so a minimal valid stub zip satisfies the embed; the SPA is not
# needed by the verifier.
COPY assets.zip /app/application/statics/assets.zip

# Pre-build cloudreve at C once (network available here) to warm the caches; a
# verifier rebuild from /app then recompiles only changed packages. -p 2 keeps
# the compiler's peak memory modest on a loaded host.
RUN go build -p 2 -o /usr/local/bin/cloudreve . \
    && /usr/local/bin/cloudreve version 2>/dev/null || /usr/local/bin/cloudreve --version 2>/dev/null || true

RUN rm -rf /app/.git

# The verifier drives the running server from Python; pytest + the stdlib HTTP
# client are all it needs (installed in a separate layer so the cached Go build
# above is reused). No network is used at verifier run time.
RUN apt-get update && apt-get install -y --no-install-recommends python3-pytest \
    && rm -rf /var/lib/apt/lists/*

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
