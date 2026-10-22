# Nhost (github.com/nhost/nhost) monorepo: the Go CLI that runs a local
# development stack, including the configuration service the local dashboard
# talks to. Everything is installed here so the task runs with NO network
# after the image is built: Go modules are vendored in the repository, and the
# verifier drives the service in-process over loopback only.
FROM golang:1.26-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git patch bash python3 \
    && rm -rf /var/lib/apt/lists/*

ENV GOTOOLCHAIN=local \
    GOPATH=/go \
    CGO_ENABLED=0

# JUnit converter for `go test` output (installed while network is available,
# outside the repository so the vendored module mode does not apply).
RUN cd / && go install github.com/jstemmer/go-junit-report/v2@v2.1.0

# The repository at the vulnerable commit; history removed further down.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/nhost/nhost \
    && git fetch -q --depth 1 origin da4e00011f773a2f219150549b2d32a1bd5ef582 \
    && git checkout -q FETCH_HEAD

# Modules come from vendor/; never reach the network for them.
ENV GOFLAGS=-mod=vendor GOPROXY=off

# Warm the build cache for the CLI (including the configuration service) and
# the shared HTTP middleware, with their test binaries, so a later `go test`
# recompiles only what changed, offline.
RUN go build ./cli/... 2>&1 | tail -5 \
    && go test -p 4 -count=1 -run '^$' \
        ./cli/cmd/configserver/... \
        ./internal/lib/oapi/... 2>&1 | tail -5

RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
