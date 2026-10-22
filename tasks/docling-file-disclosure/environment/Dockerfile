# Python 3.11: inside the project's supported range (>=3.10). The flaw is not
# Python-version dependent.
FROM python:3.11-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the vulnerable commit, then drop all git history so
# the later (fixed) history, tags and branches are not present in the image.
ARG REPO_URL=https://github.com/docling-project/docling
ARG COMMIT=e4780063bb4c33b2b48222d2106ce9ba45eaf453
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Install the project editable (so a fix under /app/docling takes effect) with
# the extras the JSON input, saved conversions and the service client need,
# plus the test runner and the in-process service fake's server libraries.
# Versions are pinned to a set verified at the pinned commit.
COPY requirements-lock.txt /tmp/requirements-lock.txt
RUN pip install --no-cache-dir -c /tmp/requirements-lock.txt \
        -e ".[convert-core,cli,service-client]" \
        "docling-core==2.98.0" "pytest>=8.1,<9" "fastapi>=0.115" "uvicorn>=0.30" \
    && python -c "import docling.document_converter, docling.service_client"

# Defensive guard: drop any text file naming the advisory. The checkout
# predates the fix, so this finds nothing today.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-p944|CVE-2026-105748' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
