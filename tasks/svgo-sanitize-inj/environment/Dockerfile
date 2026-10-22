# svgo is a Node.js library + CLI that optimizes SVG documents. The vulnerable
# code and the verifier tests run on Node 20 with the project's own toolchain.
# No network is available after this image is built: npm installs everything here.
FROM node:20-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the VULNERABLE commit, then drop its git history so the
# later (fixed) history is not present in the image.
ARG REPO_URL=https://github.com/svg/svgo
ARG COMMIT=628e3bc7336625a30365d0a9b60185307d852466
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Task sibling code (INJECTED track): applied to our copy only, never shipped
# upstream. Adds two thin resource/animation guards next to the existing one.
COPY inject.patch /tmp/inject.patch
RUN patch -p1 < /tmp/inject.patch && rm -f /tmp/inject.patch

# Install dependencies while the network is available (offline afterwards).
RUN npm install --no-audit --no-fund --no-save

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
