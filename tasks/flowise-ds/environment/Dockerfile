# Flowise is a TypeScript (Node ^20) low-code LLM app builder (pnpm monorepo).
# The server source lives in packages/server/src. The verifier runs hidden jest
# suites directly against that source with every infrastructure dependency
# (database, credential decryption, OpenAI SDK, running-app singleton) stubbed,
# so the heavyweight monorepo build is not needed and nothing is downloaded at
# test time. A small, pinned verifier toolchain is installed at /opt/verifier
# while the network is available here.
FROM node:20-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git patch python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the pinned (vulnerable) commit, then drop its git
# history so the later (fixed) history is not present in the image.
ARG REPO_URL=https://github.com/flowiseai/flowise
ARG COMMIT=700137738bcaebefd4709021f6d6b0abcd7df0ac
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Task sibling code (INJECTED track): applied to our copy only, never shipped
# upstream. Adds two thin credential-using helpers next to the existing ones.
COPY inject.patch /tmp/inject.patch
RUN patch -p1 < /tmp/inject.patch && rm -f /tmp/inject.patch

# Verifier toolchain (offline after build). babel-jest transforms the product
# TypeScript; http-status-codes is the only runtime dependency the tested modules
# import that is not stubbed.
RUN mkdir -p /opt/verifier \
    && cd /opt/verifier \
    && npm init -y >/dev/null 2>&1 \
    && npm install --no-audit --no-fund --save-exact \
        jest@29.7.0 \
        babel-jest@29.7.0 \
        jest-junit@16.0.0 \
        @babel/core@7.26.0 \
        @babel/preset-env@7.26.0 \
        @babel/preset-typescript@7.26.0 \
        @babel/plugin-proposal-decorators@7.25.9 \
        @babel/plugin-transform-class-properties@7.25.9 \
        http-status-codes@2.3.0 \
    && npm cache clean --force \
    && test -f /opt/verifier/node_modules/.bin/jest \
    && rm -rf /root/.npm

# One clean local commit (no upstream history) so the solver can diff its own work.
RUN git init -q \
    && git config --global user.name dev \
    && git config --global user.email dev@example.com \
    && git config --global --add safe.directory /app \
    && git add -A \
    && GIT_AUTHOR_DATE="2026-01-01T00:00:00" GIT_COMMITTER_DATE="2026-01-01T00:00:00" \
       git commit -q -m "Initial commit" \
    && rm -rf /root/.cache /tmp/*

# --- agent layer (harness/claude-code.Dockerfile.snippet, appended unchanged) ---
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
