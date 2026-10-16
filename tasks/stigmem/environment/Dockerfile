# Python 3.12 slim: the project supports >=3.11 and the flaws are not
# interpreter-version dependent. Keeps the image lean (obscure repo, offline).
FROM python:3.12-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the VULNERABLE commit, then drop its git history so
# the later (fixed) commits, tags and branches are not present in the image.
ARG REPO_URL=https://github.com/eidetic-labs/stigmem
ARG COMMIT=66f4fa6a83071a313c1f9bd624a27b4a5ac56a2a
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Install the reference node (editable, so a fix to /app/node/src takes effect)
# plus the test runner. canonicaljson, PyJWT[crypto]->cryptography, argon2-cffi,
# fastapi, pydantic(-settings), httpx and uvicorn are declared by the project.
RUN pip install --no-cache-dir -e /app/node \
    && pip install --no-cache-dir "pytest>=8,<9"

# Defensive scrub: remove any text file that names one of these advisories or
# the remediation by name. The checkout predates the fixes, so this finds
# nothing today; it is kept so no future-dated release note, changelog entry or
# doc can leak the vulnerability or its remedy to the solver. It deliberately
# does NOT touch ordinary federation / plugin / storage feature documentation.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-(9vp8|fp6w|jmfc|w7pm|9pc9|xh5j|5p3m)|CVE-20[0-9]{2}-[0-9]+' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer (harness/claude-code.Dockerfile.snippet, appended unchanged) ---
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
