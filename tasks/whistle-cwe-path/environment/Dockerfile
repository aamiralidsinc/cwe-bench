# whistle (HTTP/HTTPS/WebSocket debugging proxy) at the vulnerable commit
# 826b59bf, the parent of the upstream fix 777bcf69. The verifier boots the
# product's internal request-serving component in-process and drives it over
# loopback HTTP; no network is needed after the image is built.

# ---- Builder stage: fetch the vulnerable source tree, without its history ----
FROM node:20-bookworm-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG REPO_URL=https://github.com/avwo/whistle.git
ARG COMMIT=826b59bf14b7f3eca56dd5f1cc7f3152e3983005

RUN mkdir /src && cd /src \
    && git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /src/.git

# ---- Final stage ----
FROM node:20-bookworm-slim

# patch/curl/git/ca-certificates/bash for the harness and gate; python3 runs the scorer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git patch python3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /src /app
WORKDIR /app

# Runtime dependencies only, from the lockfile (network is available at build time).
# Dev tooling (webpack/babel/react) is for the browser bundle, which is already built
# into the tree, and is not needed to run or test the server.
RUN npm install --omit=dev --no-audit --no-fund --ignore-scripts \
    && test -f /app/node_modules/express/package.json \
    && test -f /app/node_modules/hagent/lib/get-server.js \
    && npm cache clean --force \
    && rm -rf /root/.npm /tmp/*

ENV CI=true

# One clean local commit (no upstream history) so the solver can diff its own changes.
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
