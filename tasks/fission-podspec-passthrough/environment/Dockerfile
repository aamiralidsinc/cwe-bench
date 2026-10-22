# Fission (github.com/fission/fission) is a Go + Kubernetes serverless
# framework. Everything is installed here so the task runs with NO network
# after the image is built. The verifier drives the admission validators and
# the controllers' deployment builders as Go unit tests against in-memory
# Kubernetes fakes, as the project's own tests do; no cluster is contacted.
FROM golang:1.26.3-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git patch bash python3 \
    && rm -rf /var/lib/apt/lists/*

# GOTOOLCHAIN=local: never download another toolchain. GOFLAGS=-mod=mod keeps
# rebuilds working from the module cache baked in below.
ENV GOTOOLCHAIN=local \
    GOFLAGS=-mod=mod \
    GOPATH=/go \
    CGO_ENABLED=0

# The repository at the vulnerable commit; history removed further down.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/fission/fission \
    && git fetch -q --depth 1 origin 8fa799417c77ce8a0189d9858bfe11ece29b84a6 \
    && git checkout -q FETCH_HEAD

RUN go mod download all

# JUnit converter for `go test` output (installed while network is available).
RUN go install github.com/jstemmer/go-junit-report/v2@v2.1.0

# Warm the build cache: the packages around Environment / Function pod
# handling, and their test binaries (testify, client-go fakes), so a later
# `go test` recompiles only what changed, offline.
RUN go test -p 2 -count=1 -run '^$' \
        ./pkg/apis/core/v1/... \
        ./pkg/webhook/... \
        ./pkg/executor/util/... \
        ./pkg/executor/executortype/... \
        ./pkg/buildermgr/... 2>&1 | tail -5

RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
