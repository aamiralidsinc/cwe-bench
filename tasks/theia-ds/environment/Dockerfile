# Eclipse Theia is a TypeScript npm-workspaces/lerna monorepo. The product and
# the hidden tests run on Node 22 with the repository's own toolchain. No network
# is available after this image is built: every dependency is installed here.
FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch python3 make g++ procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the VULNERABLE commit, then drop its git history so the
# later (fixed) history is not present in the image.
ARG REPO_URL=https://github.com/eclipse-theia/theia
ARG COMMIT=de745e95b4273fcb72358f0e34c5340beb359a74
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Task sibling code (INJECTED track): applied to our copy only, never shipped
# upstream. Adds two thin trust guards next to existing ones.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch && rm -f /tmp/injection.patch

# Install the monorepo from the committed lockfile while the network is
# available. Native/optional binaries (puppeteer, electron) are not needed for
# the browser-side code and tests.
ENV PUPPETEER_SKIP_DOWNLOAD=true \
    ELECTRON_SKIP_BINARY_DOWNLOAD=1 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    npm_config_audit=false \
    npm_config_fund=false \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0
RUN npm ci --ignore-scripts --no-audit --no-fund

# The repository's postinstall generates the shared re-export modules and the
# TypeScript project references; the compile needs both.
RUN ./node_modules/.bin/theia-patch \
    && ./node_modules/.bin/tsc --build dev-packages/private-re-exports \
    && (cd packages/core && ../../node_modules/.bin/theia-re-exports generate) \
    && (cd packages/electron && ../../node_modules/.bin/theia-re-exports generate) \
    && npm run -s compute-references

# A JUnit reporter for the verifier, kept outside the workspace the agent edits.
RUN npm install --prefix /opt/junit --no-audit --no-fund mocha-junit-reporter@2.2.1

# Compile every package the hidden tests load (references pull in the rest).
RUN ./node_modules/.bin/tsc --build \
        packages/ai-ide packages/ai-chat packages/ai-terminal \
        packages/ai-anthropic packages/ai-copilot

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
