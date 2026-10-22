# Node 20: the LTS the project's own toolchain runs on. The flaw is not
# Node-version dependent.
FROM node:20-bookworm-slim

# Tools the task and verifier need. No network is available after build.
# python3 runs the verifier's score.py (the image is a Node base).
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the pinned (vulnerable) commit.
ARG REPO_URL=https://github.com/protobufjs/protobuf.js
ARG COMMIT=1aca107aa7938d1e49a25f9653186db2f40a0253
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# Apply the task's additions to the text-format and ProtoJSON merge helpers,
# then drop the git history so no later (fixed) commit is present in the image.
COPY inject.patch /tmp/inject.patch
RUN patch -p1 < /tmp/inject.patch \
    && rm -f /tmp/inject.patch \
    && rm -rf /app/.git

# Install the project's dependencies and the CLI package's dependencies while
# the network is still available. The CLI resolves `protobufjs` via a file link
# to the parent checkout so a fix to /app takes effect.
RUN npm install --no-audit --no-fund \
    && npm install --no-save --no-audit --no-fund tmp \
    && mkdir -p cli/node_modules \
    && ln -sfn /app cli/node_modules/protobufjs \
    && for d in chalk escodegen espree estraverse glob jsdoc minimist tmp; do \
         if [ -d "node_modules/$d" ]; then ln -sfn "/app/node_modules/$d" "cli/node_modules/$d"; fi; \
       done

# Build the bundles the project's own loader tests read, and warm the test
# collection once. Everything after this is offline.
RUN npm run build:bundle >/dev/null \
    && npx tape -r ./lib/tape-adapter tests/api_textformat.js >/dev/null \
    && rm -rf /app/node_modules/.cache

# Defensive guard: drop any text file naming the advisory. The checkout predates
# the fix, so this finds nothing today.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-JFJ6-75FJ-8934|CVE-2026-59876|2335' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
