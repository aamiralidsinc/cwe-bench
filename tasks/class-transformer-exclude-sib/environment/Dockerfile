FROM node:20-bookworm-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the pinned commit, then drop its git history.
ARG REPO_URL=https://github.com/typestack/class-transformer
ARG COMMIT=a2734a5d154c9b0beb9a10555a04416bc371de06
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# The project's dependencies (jest, ts-jest, typescript, reflect-metadata) from its
# lockfile, plus a JUnit reporter for the verifier. Done now while the network is available.
RUN npm ci --ignore-scripts --no-audit --no-fund \
    && npm install --prefix /opt/junit --no-audit --no-fund jest-junit@16.0.0 \
    && npx jest --ci 2>&1 | tail -5

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
