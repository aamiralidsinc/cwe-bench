# TinaCMS is a TypeScript/Node content platform. The media adapters are plain
# TypeScript modules (next-tinacms-s3/dos/azure/cloudinary). The verifier runs
# them directly with the storage SDKs replaced by in-memory stubs, so the
# heavyweight pnpm workspace build is not needed and nothing is downloaded at
# test time. The runtime packages the adapters import are installed in a small
# verifier toolchain while the network is available here; /app/node_modules
# points at it so the product sources resolve their imports as in a normal
# install.
FROM node:22-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the pinned (vulnerable) commit, then drop its git
# history so no later (fixed) commit, tag or branch is present in the image.
ARG REPO_URL=https://github.com/tinacms/tinacms
ARG COMMIT=d08ffb40de47f8c8296646b9076af79a26d76c47
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Task sibling code (INJECTED track): applied to our copy only, never shipped
# upstream. Adds thin media routes next to the existing adapters.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch && rm -f /tmp/injection.patch

# Verifier toolchain and the runtime packages the media adapters import.
RUN mkdir -p /opt/verifier \
    && cd /opt/verifier \
    && npm init -y >/dev/null 2>&1 \
    && npm install --no-audit --no-fund --save-exact \
        vitest@2.1.9 \
        @aws-sdk/client-s3@3.744.0 \
        @aws-sdk/s3-request-presigner@3.744.0 \
        @azure/storage-blob@12.26.0 \
        cloudinary@1.41.3 \
        multer@1.4.5-lts.1 \
    && npm cache clean --force \
    && rm -rf /root/.npm \
    && test -f /opt/verifier/node_modules/vitest/vitest.mjs
RUN ln -s /opt/verifier/node_modules /app/node_modules

# One clean local commit (no upstream history) so the solver can diff its own
# work. node_modules is a verifier symlink and is excluded.
RUN git init -q \
    && printf 'node_modules\n' >> .git/info/exclude \
    && git config --global user.name dev \
    && git config --global user.email dev@example.com \
    && git config --global --add safe.directory /app \
    && git add -A \
    && GIT_AUTHOR_DATE="2026-01-01T00:00:00" GIT_COMMITTER_DATE="2026-01-01T00:00:00" \
       git commit -q -m "Initial commit" \
    && rm -rf /root/.cache /tmp/*

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
