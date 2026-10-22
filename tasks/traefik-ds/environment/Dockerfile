# Traefik (github.com/traefik/traefik, v2 branch) is a Go reverse proxy.
# Everything is installed here so the task runs with NO network after the
# image is built. The verifier drives the entry-point HTTP server and the
# middlewares in-process with Go tests over loopback only.
FROM golang:1.25-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git patch bash python3 \
    && rm -rf /var/lib/apt/lists/*

# GOTOOLCHAIN=local: never download another toolchain. GOFLAGS=-mod=mod keeps
# rebuilds working from the module cache baked in below.
ENV GOTOOLCHAIN=local \
    GOFLAGS=-mod=mod \
    GOPATH=/go \
    CGO_ENABLED=0

# The repository at the vulnerable commit.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/traefik/traefik \
    && git fetch -q --depth 1 origin 0056f09a0c4aff3cdd789bcad44a6dd196884180 \
    && git checkout -q FETCH_HEAD

# Task sibling code (INJECTED track): applied to our copy only, never shipped upstream.
COPY inject.patch /tmp/inject.patch
RUN patch -p1 < /tmp/inject.patch && rm -f /tmp/inject.patch

RUN go mod download all

# JUnit converter for `go test` output (installed while network is available).
RUN go install github.com/jstemmer/go-junit-report/v2@v2.1.0

# Warm the build cache for the entry-point server, static configuration and
# HTTP middlewares, including their test binaries, so a later `go test`
# recompiles only what changed, offline.
RUN go test -p 4 -count=1 -run '^$' \
        ./pkg/config/static/... \
        ./pkg/server/... \
        ./pkg/middlewares/... 2>&1 | tail -5 \
    && go build ./cmd/... 2>&1 | tail -5

# Drop the vulnerable repository's history so the later (fixed) history is not
# present in the image.
RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
