# Python 3.11: within the interpreter range the project supports and keeps the
# image lean. None of the flaws are Python-version dependent.
FROM python:3.11-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the vulnerable commit, then drop its git history so
# the later (fixed) history, tags and branches are not present in the image.
ARG REPO_URL=https://github.com/ronf/asyncssh
ARG COMMIT=f67234fb3c36242be0c5c9f29e1fdbbe544fc4e0
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Install the project editable (so a fix to /app/asyncssh takes effect) together
# with its one runtime dependency (cryptography) and the test runner. Done now
# while the network is available; nothing is fetched at trial time.
# The project derives its version from git via setuptools-scm, but we removed
# /app/.git above; supply the version explicitly (this checkout is the 2.14.0
# release line) so the editable build does not need the repository history.
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ASYNCSSH=2.14.0
RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir "cryptography>=39" "pytest>=7,<9"

# Scrub any mention of the advisories or the fixes from text the solver can read
# (release notes, changelog, docs). The checkout predates these fixes, so this
# finds nothing today; it is kept as a defensive guard so no shipped text can
# name a vulnerability, its CVE/GHSA id, or the function that remedies it. It
# deliberately leaves ordinary feature documentation (ssh config, scp, auth)
# untouched, since the solver may legitimately rely on it.
RUN find /app -type f \( -name '*.rst' -o -name '*.md' -o -name '*.txt' \) -print0 \
      | xargs -0 -r grep -ilE 'CVE-2023-46445|CVE-2023-46446|CVE-2026-45309|CVE-2026-54591|CVE-2026-62949|GHSA-[0-9a-z]{4}|message injection|_set_tokens|_parse_cd_args|unsafe username' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer (harness/claude-code.Dockerfile.snippet, appended unchanged) ---
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
