# Python 3.12: a version the project's declared range supports.
FROM python:3.12-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the pinned (vulnerable) commit.
ARG REPO_URL=https://github.com/berriai/litellm
ARG COMMIT=76ffefcc1c36f4e78178ca0278d38385cafa6ec6
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# Apply this task's request-handling additions, then drop the git history so no
# later (fixed) commit, tag or branch is present in the image.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /app/.git

# Install the proxy distribution (editable, so a fix to /app takes effect) and
# the test toolchain while the network is still available.
RUN pip install --no-cache-dir \
        -e ".[proxy]" \
        "prisma>=0.11.0,<1.0" \
        pytest pytest-asyncio pytest-mock respx

# Warm the import path once so first-request costs in tests stay low, then
# clear caches.
RUN python -c "import litellm, litellm.proxy.proxy_server, litellm.proxy.health_endpoints._health_endpoints, litellm.proxy.openai_files_endpoints.files_endpoints, litellm.proxy.image_endpoints.endpoints" \
    && find /app -name __pycache__ -type d -prune -exec rm -rf {} + ; true

# Defensive guard: drop any text file naming the advisory. The checkout predates
# the fix, so this finds nothing today.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' -o -name '*.json' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-3CV6-JPF6-8222|CVE-2026-84377|PYSEC-2026-4066' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
