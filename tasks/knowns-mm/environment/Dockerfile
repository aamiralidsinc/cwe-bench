# Knowns (github.com/knowns-dev/knowns, module github.com/howznguyen/knowns) is a
# Go CLI + MCP server + local web UI that keeps a project's knowledge base under
# .knowns/. Everything is installed here so the task runs with NO network after
# the image is built. The verifier drives the MCP tools and the web UI's HTTP
# handlers as Go tests against temporary project folders, as the project's own
# tests do; no server process is started.
FROM golang:1.24-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git patch bash python3 \
    && rm -rf /var/lib/apt/lists/*

# GOTOOLCHAIN=local: never download another toolchain. GOFLAGS=-mod=mod keeps
# rebuilds working from the module cache baked in below.
ENV GOTOOLCHAIN=local \
    GOFLAGS=-mod=mod \
    CGO_ENABLED=1 \
    GOPATH=/go

# The repository at the vulnerable commit; history removed further down.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/knowns-dev/knowns \
    && git fetch -q --depth 1 origin d3989829fb5095666d23d005b2f78a082832a396 \
    && git checkout -q FETCH_HEAD

# Two maintenance siblings of the same identifier-to-filename mapping, added to
# our copy only so the report has nearby variants a partial fix leaves open.
COPY inject.patch /tmp/inject.patch
RUN patch -p1 < /tmp/inject.patch \
    && rm -f /tmp/inject.patch

RUN go mod download all

# JUnit converter for `go test` output (installed while network is available).
RUN go install github.com/jstemmer/go-junit-report/v2@v2.1.0

# The web UI asset embed requires a dist directory; a stub is enough for the Go
# packages the verifier builds and tests.
RUN mkdir -p /app/ui/dist && printf '<!-- stub -->\n' > /app/ui/dist/index.html

# Warm the build cache: the storage layer, the MCP tool handlers and the web
# UI's HTTP routes, and their test binaries, so a later `go test` recompiles
# only what changed, offline.
RUN go test -p 2 -count=1 -run '^$' \
        ./internal/models/... \
        ./internal/storage/... \
        ./internal/mcp/handlers/... \
        ./internal/server/routes/... 2>&1 | tail -5

RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
