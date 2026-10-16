# Argo Workflows is a large Go + Kubernetes project (module
# github.com/argoproj/argo-workflows/v4). Everything is installed here so the
# task runs with NO network after the image is built. The verifier drives the
# argo API-server handlers and library APIs directly against a fake/in-memory
# Kubernetes client (k8s.io/client-go/kubernetes/fake), exactly as the project's
# own server unit tests do; no real cluster is ever contacted.
FROM golang:1.25-bookworm

# Tools: project build, the reference-fix patch step, the Python scorer and the
# JUnit converter used to turn `go test -json` output into the two report dirs.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git patch bash python3 gcc \
    && rm -rf /var/lib/apt/lists/*

# GOTOOLCHAIN=local pins the toolchain to this image's Go (no network download
# of another toolchain). GOFLAGS=-mod=mod lets an incremental verifier rebuild
# touch the module cache that is baked into the image below.
ENV GOTOOLCHAIN=local \
    GOFLAGS=-mod=mod \
    GOPATH=/go \
    CGO_ENABLED=1

# Fetch the repository at the VULNERABLE commit C into /app, then (later) drop
# the git history so no fixed commit is present in the image.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/argoproj/argo-workflows \
    && git fetch -q --depth 1 origin 4cac12c75de720889ad2cae8a6cc63c566b1d8d8 \
    && git checkout -q FETCH_HEAD

# Download the whole module graph once (network available here) so every later
# `go test` runs from the cache with no network.
RUN go mod download all

# Install the JUnit converter into the image (network available here).
RUN go install github.com/jstemmer/go-junit-report/v2@v2.1.0

# Warm the build cache by compiling the packages the verifier exercises (and
# their k8s dependency closure) plus their test dependencies. -p 2 caps the
# compiler's parallelism to keep peak memory modest on a loaded host. A verifier
# rebuild from /app then recompiles only changed packages, offline.
RUN go build -p 2 \
        ./server/sync/... \
        ./server/auth/... \
        ./server/workflowtemplate/... \
        ./server/clusterworkflowtemplate/... \
        ./workflow/artifacts/... \
        ./workflow/controller/... \
    && go vet -mod=mod ./server/sync/... ./workflow/artifacts/logging/... 2>/dev/null || true

# Pre-compile the test binaries so the module's test-only deps (testify, the
# client-go fakes) are built into the cache too; offline afterwards.
RUN go test -p 2 -count=1 -run '^$' \
        ./server/sync/... \
        ./server/auth/... \
        ./server/workflowtemplate/... \
        ./server/clusterworkflowtemplate/... \
        ./workflow/artifacts/logging/... \
        ./workflow/controller/... 2>&1 | tail -5 || true

RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
