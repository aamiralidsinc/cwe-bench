# Python 3.11: the version the project's own Dockerfile uses. The flaw is not
# Python-version dependent.
FROM python:3.11-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# The repository at the vulnerable commit; all git history is then dropped so the
# later (fixed) history, tags and branches are not present in the image.
ARG REPO_URL=https://github.com/hkuds/vibe-trading
ARG COMMIT=fd767f5c29c72cffe8e3f89c7ff006cb3041397f
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# The agent's dependencies (versions frozen from a verified install) and the test
# runner, while the network is up.
COPY constraints.txt /tmp/constraints.txt
RUN pip install --no-cache-dir -r agent/requirements.txt -c /tmp/constraints.txt \
    && pip install --no-cache-dir -c /tmp/constraints.txt pytest \
    && cd /app/agent && python -c "import api_server, src.tools, src.agent.loop, pandas, scipy, docx, openpyxl"

# Defensive guard: drop any text file naming the advisory. The checkout predates
# the fix, so this finds nothing today.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-5rmq-chc7-m22f' 2>/dev/null \
      | xargs -r rm -f || true

WORKDIR /app/agent

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
