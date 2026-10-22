# summarize (steipete/summarize) at the vulnerable commit cd3ee48f, the direct parent
# of the upstream fix 3c552244. Node 24 is the version the project's engines and its
# vitest 4 toolchain run on.
FROM node:24-bookworm-slim

# Tools the harness and the verifier need (git/patch for the checkout and the
# reference fix, python3 for the scorer, a compiler toolchain for native installs).
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

RUN corepack enable && corepack prepare pnpm@10.33.2 --activate

WORKDIR /app

# Fetch the repository at the VULNERABLE commit, then drop its git history so no
# later (fixed) commit, tag or branch is present in the image.
ARG REPO_URL=https://github.com/steipete/summarize.git
ARG COMMIT=cd3ee48fb24a54aa3a7653ffd84ae38616227377
RUN git init -q . \
    && git remote add origin "${REPO_URL}" \
    && git fetch -q --depth 1 origin "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# Task sibling code (INJECTED track): applied to our copy only, never shipped
# upstream. Adds an optional chapter-title fetch on the podcast flow and a
# Spotify embed transcript fetch.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 --no-backup-if-mismatch < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /app/.git

# Install every dependency and the test toolchain from the committed lockfile while
# the network is available. The root "prepare" script builds the workspace too.
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
RUN pnpm install --frozen-lockfile

# One clean local commit (no upstream history) so the solver can diff its own
# changes and the reference patch applies to a pristine tree.
RUN git init -q \
    && git config --global user.name dev \
    && git config --global user.email dev@example.com \
    && git config --global --add safe.directory /app \
    && git add -A \
    && GIT_AUTHOR_DATE="2026-01-01T00:00:00" GIT_COMMITTER_DATE="2026-01-01T00:00:00" \
       git commit -q -m "Initial commit" \
    && rm -rf /tmp/*

ENV CI=true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
