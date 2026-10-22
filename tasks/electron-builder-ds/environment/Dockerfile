# electron-builder monorepo (pnpm workspace) at the vulnerable commit 8a035f83, the parent of the
# upstream fix 22a7532b, plus this task's Gitea publisher (environment/injection.patch). The verifier
# runs vitest against the TypeScript *source* in /app (no compile step at grading time); nothing is
# downloaded after the image is built.

# ---- Builder stage: fetch the vulnerable source tree, without its history ----
FROM node:22-bookworm-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates patch \
    && rm -rf /var/lib/apt/lists/*

ARG REPO_URL=https://github.com/electron-userland/electron-builder.git
ARG COMMIT=8a035f836bb79d5346c69246530190dd72ec4519

RUN mkdir /src && cd /src \
    && git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}" "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# The task's addition: a self-hosted Gitea publisher, written the way the other publishers are.
# The upstream fix never touches it.
COPY injection.patch /tmp/injection.patch
RUN cd /src \
    && patch -p1 --no-backup-if-mismatch < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /src/.git

# ---- Final stage ----
FROM node:22-bookworm-slim

# patch/curl/git/ca-certificates/bash for the harness and gate; python3 runs the scorer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git patch python3 \
    && rm -rf /var/lib/apt/lists/*

# The repo's package manager (package.json "packageManager"), installed globally so it works
# offline without corepack downloads.
RUN npm install -g pnpm@11.1.0 && npm cache clean --force

COPY --from=builder /src /app
WORKDIR /app

# Workspace packages and the test project with their dev/test tooling (vitest, typescript) from
# the lockfile. Install scripts are skipped: they only fetch Electron and native tool binaries,
# which the unit tests do not use.
ENV ELECTRON_SKIP_BINARY_DOWNLOAD=1
RUN pnpm config set store-dir /opt/pnpm-store \
    && pnpm install --frozen-lockfile --ignore-scripts \
    && rm -rf /opt/pnpm-store /root/.cache /root/.npm /root/.local/share/pnpm \
    && test -x /app/node_modules/.bin/vitest

# Compile the workspace (`tsc --build`, as `pnpm compile` does) so the packages resolve through their
# compiled entry points, as they do for the repo's own tests.
RUN node_modules/.bin/tsc --build

# One clean local commit (no upstream history) so the solver can diff its own changes.
RUN git init -q \
    && git config --global user.name dev \
    && git config --global user.email dev@example.com \
    && git config --global --add safe.directory /app \
    && git add -A \
    && GIT_AUTHOR_DATE="2026-01-01T00:00:00" GIT_COMMITTER_DATE="2026-01-01T00:00:00" \
       git commit -q -m "Initial commit" \
    && rm -rf /root/.cache /root/.npm /tmp/*

ENV CI=true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
