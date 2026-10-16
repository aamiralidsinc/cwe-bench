# MCP TypeScript SDK (pnpm workspace) at the vulnerable commit ef39308e, the parent of the
# upstream fix edd12e28. Base environment by Hadi (2026-10-15), ported to the cwe-bench layout.
# The verifier runs vitest against the SDK *source* in /app (no build step); no network is
# needed after the image is built.

# ---- Builder stage: fetch the vulnerable source tree, without its history ----
FROM node:22-bookworm-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG REPO_URL=https://github.com/modelcontextprotocol/typescript-sdk.git
ARG COMMIT=ef39308e963496b75e50553f6265d99cacb4fbb9

RUN mkdir /src && cd /src \
    && git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /src/.git

# ---- Final stage ----
FROM node:22-bookworm-slim

# patch/curl/git/ca-certificates/bash for the harness and gate; python3 runs the scorer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git patch python3 \
    && rm -rf /var/lib/apt/lists/*

# The repo's package manager (pinned to package.json "packageManager"), installed globally so it
# works offline without corepack downloads.
RUN npm install -g pnpm@10.26.1 && npm cache clean --force

COPY --from=builder /src /app
WORKDIR /app

# Workspace libraries (client, core, core-internal, servers, middleware) with their dev/test
# tooling (vitest, typescript, tsx) from the lockfile. Examples, e2e and conformance suites are
# left out: the conformance suite pulls a published SDK release from npm.
RUN pnpm config set store-dir /opt/pnpm-store \
    && pnpm install --frozen-lockfile --ignore-scripts \
         --filter "./packages/**" --filter "./common/**" --filter "./test/helpers" \
    && rm -rf /opt/pnpm-store /root/.cache /root/.npm /root/.local/share/pnpm \
    && test -x /app/packages/client/node_modules/.bin/vitest

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

# --- agent layer (harness/claude-code.Dockerfile.snippet, appended unchanged) ---
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
