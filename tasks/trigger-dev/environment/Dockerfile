# trigger.dev is a pnpm/turbo monorepo (background-jobs platform). The webapp
# (apps/webapp, a Remix/Express server) is built and run here so the task runs
# with NO network after build. Datastores are local: Postgres + Redis in-image;
# ClickHouse is NOT run (its client is lazy — a dummy CLICKHOUSE_URL suffices,
# and run/session replication stay off), so no external services are needed.
FROM node:22-bookworm

# Tools for the build, the reference-fix patch step, the local datastores, and
# the verifier (which drives the running server over HTTP from Python).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git patch bash python3 python3-pytest \
        build-essential postgresql postgresql-contrib redis-server procps \
    && rm -rf /var/lib/apt/lists/*

RUN corepack enable && corepack prepare pnpm@10.33.2 --activate

ENV CI=1 HUSKY=0

# Fetch the repository at the VULNERABLE commit C into /app.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/triggerdotdev/trigger.dev \
    && git fetch -q --depth 1 origin bb450e608de2da1219af66a11d3a02c26a9f930b \
    && git checkout -q FETCH_HEAD

# Install the whole workspace (a filtered install chokes on the internal
# workspace deps here). Frozen lockfile = reproducible from the committed lock.
RUN pnpm install --frozen-lockfile

# Generate every Prisma client + the model catalog BEFORE building: the turbo
# build of the internal packages needs the generated clients present.
RUN pnpm --filter @trigger.dev/database run generate \
    && pnpm --filter @internal/run-ops-database run generate \
    && pnpm --filter @internal/llm-model-catalog run generate

# The bundled server externalizes a couple of transitive deps of the bundled
# @trigger.dev/* packages that pnpm's isolated store then hides at runtime.
# Have esbuild bundle them (the correct version is resolved per-import).
RUN sed -i 's#serverDependenciesToBundle: \[#serverDependenciesToBundle: [ /^eventsource-parser.*/, /^eventsource.*/,#' apps/webapp/remix.config.js

# Build the webapp and its workspace deps (turbo builds ^deps first). The
# verifier rebuilds from /app incrementally against these baked caches.
RUN pnpm run build --filter webapp

# Drop the git history so later (fixed) commits are not present in the image.
RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
