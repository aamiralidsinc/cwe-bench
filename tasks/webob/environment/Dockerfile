# Python 3.11: the flaw depends on url-joining behaviour present in CPython
# 3.10+ (leading C0 control / space characters are stripped before parsing).
FROM python:3.11-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the vulnerable commit, then drop its git history so
# the later (fixed) history is not present in the image.
ARG REPO_URL=https://github.com/pylons/webob
ARG COMMIT=54c1133c79e48940776a272f4500530e1cc3232a
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Install the project (editable, so a fix to /app/src takes effect) plus the
# test runner. Done now while the network is available.
RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir "pytest>=7,<9"

# --- agent layer (harness/claude-code.Dockerfile.snippet, appended unchanged) ---
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
