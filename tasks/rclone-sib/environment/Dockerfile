# rclone requires Go 1.26. Everything is installed here so the task runs with
# NO network after the image is built.
FROM golang:1.26-bookworm

# Tools the project build, the injection/fix patch steps, and the verifier need.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git patch bash python3 \
    && rm -rf /var/lib/apt/lists/*

# Build/module caches live at the Go defaults ($GOPATH/pkg/mod and
# /root/.cache/go-build) and are baked into the image, so a verifier run that
# rebuilds rclone from /app recompiles only the changed packages and never
# touches the network. GOTOOLCHAIN=local pins the toolchain to this image's Go.
ENV GOTOOLCHAIN=local

# Fetch the repository at the VULNERABLE parent commit into /app.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/rclone/rclone \
    && git fetch -q --depth 1 origin b3cf0444a2a3345f81d53919f38b28ef8630e6e7 \
    && git checkout -q FETCH_HEAD

# Inject the same-class authentication-bypass siblings into other serve auth
# code paths, then drop the git history so no later (fixed) commit is present.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /app/.git

# Pre-build the whole rclone binary at the (now injected) vulnerable commit.
# This downloads and compiles the entire dependency world once (network
# available here) and warms the caches; a verifier run then only recompiles
# the package(s) the solver changed.
RUN go build -o /usr/local/bin/rclone . \
    && rclone version

# The out-of-tree test harness: a standalone Go module that drives the real
# `rclone serve ...` processes over their network protocols (S3 SigV4, HTTP
# Basic, FTP and SSH) as downstream clients would. Only its module files and
# STUBS go into the image: the stubs import what the real files import, so this
# layer resolves, caches and pre-compiles every dependency. The hidden tests are
# copied in from /tests by tests/test.sh at grading time (the agent shares this
# container and could read tests baked in here).
COPY harness /opt/harness
RUN cd /opt/harness \
    && go mod tidy \
    && go build -o /usr/local/bin/authproxy ./authproxy \
    && go test -count=1 -run '^$' ./security/ ./functional/ \
    && go vet ./s3test/

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
