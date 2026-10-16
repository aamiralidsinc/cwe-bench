# better-auth (pnpm workspace) at the vulnerable commit 23094a62, the parent of the upstream
# fix 37f60cb1. The verifier runs vitest against the @better-auth/sso *source* in /app; the
# workspace libraries it depends on (better-auth, @better-auth/core) are pre-built once at image
# build time, so no build step and no network are needed after the image is built.

# ---- Builder stage: fetch the vulnerable source tree, without its history ----
FROM node:24-bookworm-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG REPO_URL=https://github.com/better-auth/better-auth.git
ARG COMMIT=23094a628f007f801be6d26e5b15dc5fc6fc4eb8

RUN mkdir /src && cd /src \
    && git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /src/.git

# ---- Final stage ----
FROM node:24-bookworm-slim

# patch/curl/git/ca-certificates/bash for the harness and gate; python3 runs the scorer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git patch python3 \
    && rm -rf /var/lib/apt/lists/*

# The repo's package manager (pinned to package.json "packageManager"), installed globally so it
# works offline without corepack downloads.
RUN npm install -g pnpm@10.30.2 && npm cache clean --force

COPY --from=builder /src /app
WORKDIR /app

ENV CI=true

# Install the full workspace from the lockfile (network is available only now, at build time),
# then pre-build the libraries @better-auth/sso resolves against so the verifier never builds.
RUN pnpm config set store-dir /opt/pnpm-store \
    && pnpm install --frozen-lockfile --ignore-scripts \
    && pnpm turbo build --filter '@better-auth/sso^...' \
    && test -f /app/node_modules/vitest/vitest.mjs \
    && test -f /app/packages/sso/node_modules/oauth2-mock-server/package.json \
    && test -d /app/packages/better-auth/dist \
    && rm -rf /opt/pnpm-store /root/.cache /root/.npm /root/.local/share/pnpm

# One clean local commit (no upstream history) so the solver can diff its own changes.
RUN git init -q \
    && git config --global user.name dev \
    && git config --global user.email dev@example.com \
    && git config --global --add safe.directory /app \
    && git add -A \
    && GIT_AUTHOR_DATE="2026-01-01T00:00:00" GIT_COMMITTER_DATE="2026-01-01T00:00:00" \
       git commit -q -m "Initial commit" \
    && rm -rf /root/.cache /root/.npm /tmp/*

# --- agent layer (harness/claude-code.Dockerfile.snippet, appended unchanged) ---
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
