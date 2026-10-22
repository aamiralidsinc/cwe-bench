# Vitest is a TypeScript test runner (pnpm monorepo). The vulnerable code and the
# verifier tests run on Node 20 with the project's own toolchain. No network is
# available after this image is built: pnpm installs everything here.
FROM node:20-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

# Pin pnpm to the version the repo expects (avoids corepack version mismatches).
RUN corepack enable && corepack prepare pnpm@10.28.2 --activate

WORKDIR /app

# Fetch the repository at the VULNERABLE commit, then drop its git history so the
# later (fixed) history is not present in the image.
ARG REPO_URL=https://github.com/vitest-dev/vitest
ARG COMMIT=76c4397b58618b6b430b0800487995c77bb6dad7
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Task sibling code (INJECTED track): applied to our copy only, never shipped
# upstream. Adds two thin file/snapshot helpers next to the existing ones.
COPY inject.patch /tmp/inject.patch
RUN patch -p1 < /tmp/inject.patch && rm -f /tmp/inject.patch

# Install the monorepo's dependencies and build every package from the committed
# lockfile while the network is available.
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
RUN pnpm install --frozen-lockfile \
    && pnpm build

# Pristine copy of the built packages for the verifier's test runner, taken
# before any agent change. Third-party dependencies stay shared through the
# node_modules link; pnpm's relative workspace links resolve inside the copy.
RUN mkdir -p /opt/vitest-verifier \
    && cp -a /app/packages /app/tsconfig.base.json /opt/vitest-verifier/ \
    && ln -s /app/node_modules /opt/vitest-verifier/node_modules

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
