# Python 3.13: a version the project's toolchain supports (requires-python
# >=3.10). The flaw is not Python-version dependent.
FROM python:3.13-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repo at the pinned (vulnerable) commit.
ARG REPO_URL=https://github.com/sooperset/mcp-atlassian
ARG COMMIT=4067d1db4097755cc6add87f95fe3f0746c98c0b
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# Apply the task's source delta, then drop the git history so no later (fixed)
# commit, tag or branch is present in the image.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /app/.git

# Install the runtime package (editable, so a fix to /app takes effect) plus the
# project's test toolchain, while the network is still available.
RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir \
        "pytest>=8.0.0" "pytest-asyncio>=0.23.0" "pytest-anyio>=0.0.0" \
    && python -c "import mcp_atlassian.jira.issues, mcp_atlassian.servers.jira, mcp_atlassian.servers.confluence"

# Defensive guard: drop any text file naming the advisory. The checkout predates
# the fix, so this finds nothing today.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-2XJ6-XX86-CWWC|CVE-2026-77255|PYSEC-2026-4080' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
