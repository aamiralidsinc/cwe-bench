# SeaweedFS (github.com/seaweedfs/seaweedfs) is a distributed object store with
# an S3 gateway, an S3 Tables API and an Iceberg REST catalog. Everything is
# installed here so the task runs with NO network after the image is built.
# The verifier drives the S3 gateway, the Iceberg catalog and the admin shell
# in-process with Go tests over loopback only.
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
    && git remote add origin https://github.com/seaweedfs/seaweedfs \
    && git fetch -q --depth 1 origin b56d155b315777dab97caea4380528ace087b529 \
    && git checkout -q FETCH_HEAD

# Task-local table-management operations (kept out of the published history):
# batch deletes, bucket usage summaries and a catalog-wide table index.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 --forward --no-backup-if-mismatch < /tmp/injection.patch \
    && rm -f /tmp/injection.patch

RUN go mod download all

# JUnit converter for `go test` output (installed while network is available).
RUN go install github.com/jstemmer/go-junit-report/v2@v2.1.0

# Warm the build cache for the S3 gateway, the S3 Tables API, the Iceberg
# catalog and the admin shell, including their test binaries, so a later
# `go test` recompiles only what changed, offline.
RUN go test -p 4 -count=1 -run '^$' \
        ./weed/s3api/ \
        ./weed/s3api/s3tables/ \
        ./weed/s3api/iceberg/ \
        ./weed/shell/ 2>&1 | tail -5 \
    && go build ./weed/ 2>&1 | tail -5

RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
