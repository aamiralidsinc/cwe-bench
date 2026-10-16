FROM python:3.12-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the pinned commit, then drop its git history.
ARG REPO_URL=https://github.com/marshmallow-code/marshmallow
ARG COMMIT=d08471b17880c62b789971ada638707a11d3f8d4
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Install the library (editable, so a fix to /app/src takes effect) plus the
# project's test requirements. Done now while the network is available.
RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir "pytest>=8,<9" simplejson

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
