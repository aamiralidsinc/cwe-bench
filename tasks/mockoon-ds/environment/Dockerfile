# Mockoon monorepo (github.com/mockoon/mockoon): the server library, its CLI and
# serverless wrappers. Everything is installed here so the task runs with NO
# network after the image is built; the verifier drives real HTTP/WebSocket
# listeners in-process on loopback only.
FROM node:24-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        patch curl ca-certificates bash git python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Project source at the pinned (pre-fix) commit; history removed further down.
RUN git init -q \
    && git remote add origin https://github.com/mockoon/mockoon \
    && git fetch -q --depth 1 origin b42bdfb7f82e83f0e81bea8e6fe41adf5ec82585 \
    && git checkout -q FETCH_HEAD

# Task-local change (kept out of the published history).
COPY injection.patch /tmp/injection.patch
RUN patch -p1 -d /app < /tmp/injection.patch && rm -f /tmp/injection.patch

# Workspace dependencies for the server library, its wrappers and the CLI.
# Installed while the build has network; nothing is fetched at test time.
RUN npm ci \
        --workspace @mockoon/commons \
        --workspace @mockoon/commons-server \
        --workspace @mockoon/serverless \
        --workspace @mockoon/cli \
        --include-workspace-root \
        --no-audit --no-fund --loglevel=error

# Build the shared libraries so the wrappers and project tests run offline.
RUN npm run build:commons \
    && npm run build:commons-server \
    && npm run build --workspace=@mockoon/serverless

RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
