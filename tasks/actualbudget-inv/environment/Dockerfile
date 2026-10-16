# Actual Budget is a local-first budgeting app with a Node/TypeScript sync
# server (package @actual-app/sync-server) in a yarn monorepo. The verifier
# drives the sync server's Express handlers over HTTP (supertest) against an
# on-disk SQLite account database, so no network and no external services are
# needed after the image is built. We install only the sync-server package's
# own dependencies with npm (the single workspace dependency @actual-app/web is
# only used to locate the static web-root and is stubbed), which keeps the image
# lean and the install reliable offline.
FROM node:22-bookworm-slim

# patch/curl/git/ca-certificates are required by the harness and gate; python3
# runs the verifier scorer; build-essential/python3 are a fallback for native
# modules (better-sqlite3, bcrypt normally install prebuilt binaries).
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch python3 python3-minimal \
    && rm -rf /var/lib/apt/lists/*

# Fetch the repository at the VULNERABLE commit C (tag v26.2.0) and drop history
# so the later (fixed) commits are not present in the image.
WORKDIR /app
ARG REPO_URL=https://github.com/actualbudget/actual
ARG COMMIT=0d6742664b7a5f111013bc6392bf3fda5e2c8a7c
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Install the sync-server package's dependencies (incl. dev deps: vitest,
# supertest, typescript). The install is done in an isolated directory so npm
# does not walk up to the monorepo root (whose `workspaces` field would pull in
# every sibling package and its `workspace:` protocol deps); the resulting
# node_modules is then moved into the package. The one workspace dependency
# (@actual-app/web) is stripped for the install and replaced with a tiny stub,
# because the server only uses it to resolve the static web-root path and the
# verifier never serves the frontend. --legacy-peer-deps avoids an npm-10
# arborist peer-resolution crash; the dependency set itself is unaffected.
RUN mkdir -p /opt/ssinstall \
    && node -e "const p=require('/app/packages/sync-server/package.json');delete p.dependencies['@actual-app/web'];require('fs').writeFileSync('/opt/ssinstall/package.json',JSON.stringify(p,null,2));" \
    && cd /opt/ssinstall \
    && npm install --legacy-peer-deps --no-audit --no-fund --loglevel=error \
    && cd /app \
    && mv /opt/ssinstall/node_modules /app/packages/sync-server/node_modules \
    && mkdir -p /app/packages/sync-server/node_modules/@actual-app/web/build \
    && printf '{"name":"@actual-app/web","version":"0.0.0","main":"index.js"}\n' > /app/packages/sync-server/node_modules/@actual-app/web/package.json \
    && printf '// stub: the sync server only needs this package to locate a web root\n' > /app/packages/sync-server/node_modules/@actual-app/web/index.js \
    && rm -rf /opt/ssinstall \
    && npm cache clean --force

WORKDIR /app

# --- agent layer (harness/claude-code.Dockerfile.snippet, appended unchanged) ---
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
