# Python 3.12: a version the project's own toolchain supports. The flaw is not
# Python-version dependent.
FROM python:3.12-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the monorepo at the pinned (vulnerable) commit.
ARG REPO_URL=https://github.com/microsoft/prompty
ARG COMMIT=90171a7738f9ff5a186416381cbfad9077cdf637
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# Inject the same-class, author-controlled file-read siblings into other
# reference-resolution paths of the loader, then drop the git history so no
# later (fixed) commit, tag or branch is present in the image.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /app/.git

# Install the Python runtime (editable, so a fix to /app takes effect) plus the
# test runner, while the network is still available.
RUN pip install --no-cache-dir -e runtime/python/prompty \
    && pip install --no-cache-dir "pytest>=8,<9" "pytest-asyncio>=0.23" \
    && python -c "import prompty; from prompty.providers.openai.executor import _project_prompty_tool"

# Defensive guard: drop any text file naming the advisory. The checkout predates
# the fix, so this finds nothing today.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-wxhm-2mq7-7697|CVE-2026-53598|PYSEC-2026-3538' 2>/dev/null \
      | xargs -r rm -f || true

WORKDIR /app/runtime/python/prompty

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
