# Go 1.26 is the version the kernel module declares (kernel/go.mod).
FROM golang:1.26-bookworm

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the pinned (vulnerable) commit.
ARG REPO_URL=https://github.com/siyuan-note/siyuan
ARG COMMIT=fd6d23d7bbe84da9f24286e7485453ca84831f48
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# Apply the task's additions (the two static-resource routes present in this
# workspace build), then drop the git history so no later commit is present in
# the image.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /app/.git

# Download every module and compile the kernel packages and their tests while
# the network is still available. CGO is required by the sqlite driver.
RUN cd /app/kernel \
    && CGO_ENABLED=1 GOFLAGS=-mod=mod go mod download \
    && CGO_ENABLED=1 GOFLAGS=-mod=mod go test -run '^$' ./server/ ./api/ ./model/ >/dev/null

# Defensive guard: drop any text file naming the advisory. The checkout predates
# the fix, so this finds nothing today.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-FGMR-7W36-9QFQ|CVE-2026-72796|GO-2026-6423' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
